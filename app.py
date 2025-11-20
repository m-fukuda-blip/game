import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Game with Ranking", layout="wide")
st.title("🎮 アクションゲーム：ランキング実装版")
st.caption("機能：❤️ライフ制 / 🆙レベルアップ / ☁️背景 / 🔊効果音 / 🏆ランキング(ブラウザ保存)")
st.write("操作方法: **W** ジャンプ / **A** 左移動 / **D** 右移動 / **R** リセット")

# ゲーム本体のHTML/JSコード
game_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  /* --- 基本スタイル --- */
  body { margin: 0; overflow: hidden; background-color: #222; color: white; font-family: 'Courier New', sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; }
  canvas { background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); image-rendering: pixelated; }
  
  /* --- UIレイヤー --- */
  #ui-layer { position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; pointer-events: none; text-shadow: 1px 1px 0 #fff;}
  #hearts { color: red; font-size: 30px; }

  /* --- ゲームオーバー・ランキング画面 --- */
  #overlay { 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
    background: rgba(0, 0, 0, 0.85); border: 4px solid white; border-radius: 10px;
    padding: 30px; text-align: center; color: white; display: none; width: 400px;
  }
  h2 { margin-top: 0; color: yellow; text-shadow: 2px 2px #f00; }
  
  /* --- ランキングテーブル --- */
  table { width: 100%; border-collapse: collapse; margin: 15px 0; }
  th, td { border-bottom: 1px solid #555; padding: 5px; text-align: left; }
  th { color: #aaa; }
  .rank-col { width: 40px; text-align: center; }
  .score-col { text-align: right; color: #0f0; }
  
  /* --- 入力フォーム --- */
  #input-section { margin-bottom: 20px; display: none; }
  input[type="text"] { padding: 5px; font-size: 16px; width: 150px; text-align: center; }
  button { padding: 5px 15px; font-size: 16px; cursor: pointer; background: #f00; color: white; border: none; font-weight: bold; }
  button:hover { background: #ff5555; }
  
  .restart-msg { margin-top: 20px; font-size: 14px; color: #ccc; }
</style>
</head>
<body>

<!-- UI表示 -->
<div id="ui-layer">
    Score: <span id="score">0</span> | Level: <span id="level">1</span><br>
    Life: <span id="hearts">❤️❤️❤️</span>
</div>

<!-- キャンバス -->
<canvas id="gameCanvas" width="800" height="400"></canvas>

<!-- オーバーレイ（ランキング＆ゲームオーバー） -->
<div id="overlay">
    <h2 id="overlay-title">GAME OVER</h2>
    <div id="final-score-display" style="font-size: 24px; margin-bottom: 15px;"></div>
    
    <!-- 名前入力エリア（ランクイン時のみ表示） -->
    <div id="input-section">
        <p style="color: cyan;">🎉 NEW RECORD! 🎉</p>
        <input type="text" id="player-name" placeholder="Enter Name" maxlength="8">
        <button onclick="submitScore()">Save</button>
    </div>

    <!-- ランキング表 -->
    <div id="ranking-section">
        <table>
            <thead><tr><th class="rank-col">#</th><th>Name</th><th class="score-col">Score</th></tr></thead>
            <tbody id="ranking-body"></tbody>
        </table>
    </div>

    <div class="restart-msg">Press 'R' to Restart</div>
</div>

<script>
  // ==========================================
  // 初期設定
  // ==========================================
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  const scoreEl = document.getElementById('score');
  const levelEl = document.getElementById('level');
  const heartsEl = document.getElementById('hearts');
  
  // UI要素
  const overlay = document.getElementById('overlay');
  const inputSection = document.getElementById('input-section');
  const rankingBody = document.getElementById('ranking-body');
  const finalScoreDisplay = document.getElementById('final-score-display');
  const nameInput = document.getElementById('player-name');

  // 画像読み込み
  const playerImg = new Image(); playerImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/player.png";
  const enemyImg = new Image(); enemyImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/enemy.png";
  const itemImg = new Image(); itemImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png";

  // ゲーム変数
  const GRAVITY = 0.6;
  const FRICTION = 0.8;
  const GROUND_Y = 360;

  let score = 0;
  let level = 1;
  let gameSpeed = 1.0;
  let hp = 3;
  let gameOver = false;
  let frameCount = 0;
  let nextEnemySpawn = 0;
  let nextItemSpawn = 0;
  let facingRight = true;
  let isInvincible = false;
  let invincibleTimer = 0;

  const player = { x: 100, y: 300, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false };
  let enemies = [];
  let items = [];
  let clouds = [];
  const keys = { right: false, left: false, up: false };

  // 音声コンテキスト
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // ==========================================
  // ランキング機能 (LocalStorage)
  // ==========================================
  const STORAGE_KEY = 'streamlit_game_ranking';

  function getRankings() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  }

  function saveRankings(rankings) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(rankings));
  }

  function checkRankIn(currentScore) {
    const rankings = getRankings();
    // まだ10人いない、または10位のスコアより高い場合
    if (rankings.length < 10) return true;
    return currentScore > rankings[rankings.length - 1].score;
  }

  function submitScore() {
    const name = nameInput.value.trim() || "NO NAME";
    let rankings = getRankings();
    
    rankings.push({ name: name, score: score });
    // スコア降順でソート
    rankings.sort((a, b) => b.score - a.score);
    // 上位10件のみ保持
    rankings = rankings.slice(0, 10);
    
    saveRankings(rankings);
    
    // UI更新
    inputSection.style.display = 'none';
    showRankingTable();
  }

  function showRankingTable() {
    const rankings = getRankings();
    rankingBody.innerHTML = "";
    
    // 枠が足りないときのために空データを埋める表示用ロジック
    for (let i = 0; i < 10; i++) {
        let r = rankings[i];
        let row = document.createElement('tr');
        if (r) {
            // 今回のスコアをハイライト
            let style = (r.score === score && inputSection.style.display === 'none') ? "color: yellow; font-weight:bold;" : "";
            row.innerHTML = `<td class="rank-col">${i + 1}</td><td style="${style}">${r.name}</td><td class="score-col">${r.score}</td>`;
        } else {
            row.innerHTML = `<td class="rank-col">${i + 1}</td><td>---</td><td class="score-col">0</td>`;
        }
        rankingBody.appendChild(row);
    }
  }

  function handleGameOver() {
    gameOver = true;
    overlay.style.display = 'block';
    finalScoreDisplay.innerText = "Final Score: " + score;
    nameInput.value = ""; // 入力欄リセット

    // ランクイン判定
    if (score > 0 && checkRankIn(score)) {
        inputSection.style.display = 'block';
        // キーボードイベントがゲーム操作と干渉しないようにフォーカス時に対策が必要だが
        // ゲームオーバー時はupdateが止まるので大丈夫
        nameInput.focus();
    } else {
        inputSection.style.display = 'none';
    }
    
    showRankingTable();
  }

  // ==========================================
  // ゲームロジック
  // ==========================================
  
  function playSound(type) {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;

    if (type === 'jump') {
        osc.type = 'square'; osc.frequency.setValueAtTime(150, now); osc.frequency.linearRampToValueAtTime(300, now + 0.1);
        gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
        osc.start(now); osc.stop(now + 0.1);
    } else if (type === 'coin') {
        osc.type = 'sine'; osc.frequency.setValueAtTime(1200, now); osc.frequency.setValueAtTime(1600, now + 0.05);
        gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.start(now); osc.stop(now + 0.2);
    } else if (type === 'hit') {
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, now); osc.frequency.linearRampToValueAtTime(50, now + 0.3);
        gain.gain.setValueAtTime(0.2, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc.start(now); osc.stop(now + 0.3);
    }
  }

  document.addEventListener('keydown', (e) => {
    // 名前入力中はゲーム操作を無効化
    if (document.activeElement === nameInput) {
        if (e.key === 'Enter') submitScore();
        return;
    }

    if (e.code === 'KeyD') { keys.right = true; facingRight = true; }
    if (e.code === 'KeyA') { keys.left = true; facingRight = false; }
    if (e.code === 'KeyW') { if (!player.jumping && !gameOver) { player.jumping = true; player.dy = -12; playSound('jump'); } }
    if (e.code === 'KeyR' && gameOver) resetGame();
  });

  document.addEventListener('keyup', (e) => {
    if (e.code === 'KeyD') keys.right = false;
    if (e.code === 'KeyA') keys.left = false;
  });

  function spawnEnemy() {
    const type = Math.random() < 0.5 ? 'ground' : 'flying';
    let speedBase = Math.random() * 3 + 2;
    let enemy = { x: canvas.width, y: 0, width: 35, height: 35, dx: -(speedBase * gameSpeed), dy: 0, type: type, angle: 0 };
    if (type === 'ground') enemy.y = GROUND_Y - enemy.height;
    else enemy.y = Math.random() * 80 + 200;
    enemies.push(enemy);
    let spawnRate = Math.max(20, 60 - (level * 5)); 
    nextEnemySpawn = frameCount + Math.random() * spawnRate + spawnRate;
  }

  function spawnItem() {
    items.push({ x: canvas.width, y: Math.random() * 150 + 150, width: 30, height: 30, dx: -2 });
    nextItemSpawn = frameCount + Math.random() * 60 + 40;
  }
  
  function initClouds() {
    clouds = [];
    for(let i=0; i<5; i++) clouds.push({x: Math.random() * canvas.width, y: Math.random() * 150, speed: Math.random() * 0.5 + 0.2});
  }

  function updateClouds() {
    for(let c of clouds) {
        c.x -= c.speed;
        if(c.x < -100) { c.x = canvas.width; c.y = Math.random() * 150; }
    }
  }

  function updateLevel() {
    const newLevel = Math.floor(score / 500) + 1;
    if (newLevel > level) {
        level = newLevel;
        gameSpeed = 1.0 + (level * 0.1);
        levelEl.innerText = level;
        if(hp < 3) { hp++; updateHearts(); }
        playSound('coin'); 
    }
  }

  function updateHearts() {
    let h = ""; for(let i=0; i<hp; i++) h += "❤️"; heartsEl.innerText = h;
  }

  function resetGame() {
    player.x = 100; player.y = 300; player.dx = 0; player.dy = 0;
    score = 0; level = 1; gameSpeed = 1.0; hp = 3;
    enemies = []; items = []; gameOver = false; frameCount = 0;
    isInvincible = false; nextEnemySpawn = 50; nextItemSpawn = 30;
    scoreEl.innerText = score; levelEl.innerText = level; updateHearts();
    initClouds();
    overlay.style.display = 'none'; // オーバーレイを隠す
    loop();
  }

  function update() {
    if (gameOver) return;
    frameCount++;
    updateClouds();
    
    if (isInvincible) { invincibleTimer--; if (invincibleTimer <= 0) isInvincible = false; }

    if (keys.right) player.dx = player.speed;
    else if (keys.left) player.dx = -player.speed;
    else player.dx *= FRICTION;

    player.x += player.dx; player.y += player.dy; player.dy += GRAVITY;

    if (player.y + player.height > GROUND_Y) { player.y = GROUND_Y - player.height; player.dy = 0; player.jumping = false; }
    if (player.x < 0) player.x = 0;
    if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

    if (frameCount >= nextEnemySpawn) spawnEnemy();
    if (frameCount >= nextItemSpawn) spawnItem();

    for (let i = 0; i < items.length; i++) {
      let item = items[i]; item.x += item.dx;
      if (item.x + item.width < 0) { items.splice(i, 1); i--; continue; }
      if (player.x < item.x + item.width && player.x + player.width > item.x && player.y < item.y + item.height && player.y + player.height > item.y) {
        score += 50; scoreEl.innerText = score; items.splice(i, 1); i--; playSound('coin'); updateLevel();
      }
    }

    for (let i = 0; i < enemies.length; i++) {
      let e = enemies[i]; e.x += e.dx;
      if (e.type === 'flying') { e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }
      if (e.x + e.width < 0) { enemies.splice(i, 1); i--; continue; }
      if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {
        if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {
          enemies.splice(i, 1); i--; player.dy = -10; score += 100; scoreEl.innerText = score; playSound('coin'); updateLevel();
        } else {
          if (!isInvincible) {
              hp--; updateHearts(); playSound('hit');
              if (hp <= 0) {
                // ゲームオーバー処理を呼び出し
                handleGameOver();
              } else {
                isInvincible = true; invincibleTimer = 60; enemies.splice(i, 1); i--;
              }
          }
        }
      }
    }
  }

  function drawObj(img, x, y, w, h, fallbackColor) {
    if (img.complete && img.naturalHeight !== 0) ctx.drawImage(img, x, y, w, h);
    else { ctx.fillStyle = fallbackColor; ctx.fillRect(x, y, w, h); }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#87CEEB'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    for(let c of clouds) { ctx.beginPath(); ctx.arc(c.x, c.y, 30, 0, Math.PI * 2); ctx.arc(c.x + 25, c.y - 10, 35, 0, Math.PI * 2); ctx.arc(c.x + 50, c.y, 30, 0, Math.PI * 2); ctx.fill(); }
     
    ctx.fillStyle = '#654321'; ctx.fillRect(0, GROUND_Y, canvas.width, 40);
    ctx.fillStyle = '#228B22'; ctx.fillRect(0, GROUND_Y, canvas.width, 10);

    for (let item of items) drawObj(itemImg, item.x, item.y, item.width, item.height, 'gold');
    for (let e of enemies) drawObj(enemyImg, e.x, e.y, e.width, e.height, 'red');

    ctx.save();
    if (isInvincible && Math.floor(Date.now() / 100) % 2 === 0) ctx.globalAlpha = 0.5;
    if (!facingRight) { ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); drawObj(playerImg, 0, 0, player.width, player.height, 'blue'); } 
    else { drawObj(playerImg, player.x, player.y, player.width, player.height, 'blue'); }
    ctx.restore();
  }

  function loop() {
    update();
    draw();
    if (!gameOver) requestAnimationFrame(loop);
  }

  resetGame();

</script>
</body>
</html>
"""

components.html(game_html, height=500)
