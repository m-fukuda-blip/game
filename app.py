import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Game with Global Ranking", layout="wide")
st.title("🎮 アクションゲーム：強敵＋段差＆穴コース版")
st.caption("機能：❤️ライフ制 / 🆙レベルアップ / ☁️背景 / 🔊効果音 / 🏆グローバルランキング実装！")
st.write("操作方法: **W** ジャンプ / **A** 左移動 / **D** 右移動 / **R** リセット")

# ==========================================
# 👇 ここに GAS (Google Apps Script) のウェブアプリURLを貼ってください
# ==========================================
GAS_API_URL = "https://script.google.com/macros/s/AKfycbxMxXwluhonVbnunqMc11rJv5rCQhUDcmm6ZTKLyMxyBeVtjKkSCCeI6FHj4V4An8MLgw/exec"

# ゲーム本体のHTML/JSコード
game_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  /* --- 基本スタイル --- */
  body {{ margin: 0; overflow: hidden; background-color: #222; color: white; font-family: 'Courier New', sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; }}
  canvas {{ background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); image-rendering: pixelated; }}
  
  /* --- UIレイヤー --- */
  #ui-layer {{ position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; pointer-events: none; text-shadow: 1px 1px 0 #fff;}}
  #hearts {{ color: red; font-size: 30px; }}

  /* --- ゲームオーバー・ランキング画面 --- */
  #overlay {{ 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
    background: rgba(0, 0, 0, 0.85); border: 4px solid white; border-radius: 10px;
    padding: 30px; text-align: center; color: white; display: none; width: 400px;
  }}
  h2 {{ margin-top: 0; color: yellow; text-shadow: 2px 2px #f00; }}
  
  /* --- ランキングテーブル --- */
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  th, td {{ border-bottom: 1px solid #555; padding: 5px; text-align: left; }}
  th {{ color: #aaa; }}
  .rank-col {{ width: 40px; text-align: center; }}
  .score-col {{ text-align: right; color: #0f0; }}
  
  /* --- 入力フォーム --- */
  #input-section {{ margin-bottom: 20px; display: none; }}
  input[type="text"] {{ padding: 5px; font-size: 16px; width: 150px; text-align: center; }}
  button {{ padding: 5px 15px; font-size: 16px; cursor: pointer; background: #f00; color: white; border: none; font-weight: bold; }}
  button:hover {{ background: #ff5555; }}
  button:disabled {{ background: #555; cursor: not-allowed; }}
  
  /* --- ローディング表示 --- */
  #loading-msg {{ 
      display: none; 
      color: yellow; 
      font-weight: bold; 
      margin-top: 10px; 
      animation: blink 1s infinite; 
  }}
  @keyframes blink {{ 50% {{ opacity: 0.5; }} }}

  .restart-msg {{ margin-top: 20px; font-size: 14px; color: #ccc; }}
</style>
</head>
<body>

<div id="ui-layer">
    Score: <span id="score">0</span> | Level: <span id="level">1</span><br>
    Life: <span id="hearts">❤️❤️❤️</span>
</div>

<canvas id="gameCanvas" width="800" height="400"></canvas>

<div id="overlay">
    <h2 id="overlay-title">GAME OVER</h2>
    <div id="final-score-display" style="font-size: 24px; margin-bottom: 15px;"></div>
    
    <div id="input-section">
        <p style="color: cyan;">🎉 NEW RECORD! 🎉</p>
        <input type="text" id="player-name" placeholder="Enter Name" maxlength="8">
        <button id="submit-btn" onclick="submitScore()">Save</button>
        <div id="loading-msg">⏳ Saving to Global Ranking...</div>
    </div>

    <div id="ranking-section">
        <div id="rank-loading" style="color:#aaa; display:none;">Loading Ranking...</div>
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
  const submitBtn = document.getElementById('submit-btn');
  const loadingMsg = document.getElementById('loading-msg');
  const rankLoading = document.getElementById('rank-loading');

  // 画像読み込み
  const playerImg = new Image(); playerImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/player.png";
  const enemyImg = new Image(); enemyImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/enemy.png";
  const enemy2Img = new Image(); enemy2Img.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/enemy2.png";
  const itemImg = new Image(); itemImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png";

  // ゲーム変数
  const GRAVITY = 0.6;
  const FRICTION = 0.8;
  const BASE_GROUND_Y = 360;  
  
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
  let terrainSegments = [];
  const player = {{ x: 100, y: 0, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false }};
  let enemies = [];
  let items = [];
  let clouds = [];
  const keys = {{ right: false, left: false, up: false }};

  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // ==========================================
  // ★ API設定 (GAS)
  // ==========================================
  const API_URL = "{GAS_API_URL}";
  let globalRankings = [];

  // ランキング取得
  async function fetchRankings() {{
    try {{
        const response = await fetch(API_URL);
        const data = await response.json();
        return data;
    }} catch (e) {{
        console.error("Error fetching ranking:", e);
        return [];
    }}
  }}

  // スコア送信
  async function sendScore(name, score) {{
    try {{
        await fetch(API_URL, {{
            method: 'POST',
            body: JSON.stringify({{ name: name, score: score }})
        }});
    }} catch (e) {{
        console.error("Error sending score:", e);
    }}
  }}

  // 起動時にランキングロード
  fetchRankings().then(data => {{
      globalRankings = data;
  }});

  function checkRankIn(currentScore) {{
    if (globalRankings.length < 10) return true;
    return currentScore > globalRankings[globalRankings.length - 1].score;
  }}

  // ★送信ボタン処理（Saving表示を追加）
  async function submitScore() {{
    const name = nameInput.value.trim() || "NO NAME";
    
    // 1. UIを送信中モードにする
    nameInput.disabled = true;
    submitBtn.disabled = true;
    loadingMsg.style.display = 'block'; // "Saving..." 表示ON
    
    // 2. 送信処理
    await sendScore(name, score);
    
    // 3. 最新ランキング再取得
    globalRankings = await fetchRankings();
    
    // 4. UIを元に戻して入力欄を消す
    loadingMsg.style.display = 'none'; // "Saving..." 表示OFF
    nameInput.disabled = false;
    submitBtn.disabled = false;
    inputSection.style.display = 'none';
    
    // 5. ランキング更新
    showRankingTable(globalRankings);
  }}

  function showRankingTable(rankings) {{
    if (!rankings) rankings = globalRankings;
    rankingBody.innerHTML = "";
    
    for (let i = 0; i < 10; i++) {{
        let r = rankings[i];
        let row = document.createElement('tr');
        if (r) {{
            // 名前とスコアが一致したら黄色にする（簡易的な自分判定）
            let style = (r.score === score && r.name === nameInput.value) ? "color: yellow; font-weight:bold;" : "";
            row.innerHTML = `<td class="rank-col">${{i + 1}}</td><td style="${{style}}">${{r.name}}</td><td class="score-col">${{r.score}}</td>`;
        }} else {{
            row.innerHTML = `<td class="rank-col">${{i + 1}}</td><td>---</td><td class="score-col">0</td>`;
        }}
        rankingBody.appendChild(row);
    }}
  }}

  function handleGameOver() {{
    gameOver = true;
    overlay.style.display = 'block';
    finalScoreDisplay.innerText = "Final Score: " + score;
    nameInput.value = "";
    
    // ローディング中を表示
    rankingBody.innerHTML = ""; 
    rankLoading.style.display = "block";

    // ゲームオーバー時に最新ランキングを取得してから判定
    fetchRankings().then(data => {{
        globalRankings = data;
        rankLoading.style.display = "none";
        showRankingTable(globalRankings);

        // ランクイン判定
        if (score > 0 && checkRankIn(score)) {{
            inputSection.style.display = 'block';
            nameInput.focus();
        }} else {{
            inputSection.style.display = 'none';
        }}
    }});
  }}

  // ==========================================
  // 以下、ゲームロジック（変更なし）
  // ==========================================
  
  function playSound(type) {{
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    
    if (type === 'jump') {{
        osc.type = 'square'; osc.frequency.setValueAtTime(150, now); osc.frequency.linearRampToValueAtTime(300, now + 0.1);
        gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
        osc.start(now); osc.stop(now + 0.1);
    }} else if (type === 'coin') {{
        osc.type = 'sine'; osc.frequency.setValueAtTime(1200, now); osc.frequency.setValueAtTime(1600, now + 0.05);
        gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.start(now); osc.stop(now + 0.2);
    }} else if (type === 'hit') {{
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, now); osc.frequency.linearRampToValueAtTime(50, now + 0.3);
        gain.gain.setValueAtTime(0.2, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc.start(now); osc.stop(now + 0.3);
    }}
  }}

  document.addEventListener('keydown', (e) => {{
    if (document.activeElement === nameInput) {{
        if (e.key === 'Enter' && !submitBtn.disabled) submitScore();
        return;
    }}
    if (['KeyW', 'KeyA', 'KeyD', 'KeyR'].includes(e.code)) {{
        e.preventDefault();
    }}
    if (e.code === 'KeyD') {{ keys.right = true; facingRight = true; }}
    if (e.code === 'KeyA') {{ keys.left = true; facingRight = false; }}
    if (e.code === 'KeyW') {{ 
        if (!player.jumping && !gameOver) {{ 
            player.jumping = true; 
            player.dy = -12; 
            playSound('jump'); 
        }} 
    }}
    if (e.code === 'KeyR' && gameOver) resetGame();
  }});

  document.addEventListener('keyup', (e) => {{
    if (e.code === 'KeyD') keys.right = false;
    if (e.code === 'KeyA') keys.left = false;
  }});

  function generateCourse() {{
    terrainSegments = [];
    let x = 0;
    let prevLevel = 0;
    const SEG_HEIGHTS = [BASE_GROUND_Y, BASE_GROUND_Y - 40, BASE_GROUND_Y - 80];

    while (x < canvas.width + 100) {{
        let width = Math.random() * 120 + 80;
        let gapWidth = 0;
        if (x > 250 && Math.random() < 0.25) {{
            gapWidth = Math.random() * 80 + 60;
        }}
        x += gapWidth;
        let delta = Math.floor(Math.random() * 3) - 1;
        let newLevel = Math.min(2, Math.max(0, prevLevel + delta));
        prevLevel = newLevel;
        const topY = SEG_HEIGHTS[newLevel];
        terrainSegments.push({{ x: x, width: width, topY: topY }});
        x += width;
    }}
  }}

  function getGroundYUnderPlayer() {{
    let groundY = null;
    for (let seg of terrainSegments) {{
        if (player.x + player.width > seg.x && player.x < seg.x + seg.width) {{
            if (groundY === null || seg.topY < groundY) {{
                groundY = seg.topY;
            }}
        }}
    }}
    return groundY;
  }}

  function getGroundYAtX(x) {{
    let groundY = null;
    for (let seg of terrainSegments) {{
        if (x >= seg.x && x <= seg.x + seg.width) {{
            if (groundY === null || seg.topY < groundY) {{
                groundY = seg.topY;
            }}
        }}
    }}
    return groundY;
  }}

  function spawnEnemy() {{
    let type = Math.random() < 0.5 ? 'ground' : 'flying';
    let speedBase = Math.random() * 3 + 2;
    if (score >= 2000 && Math.random() < 0.3) {{
        type = 'hard';
        speedBase = 7;
    }}
    let enemy = {{ 
        x: canvas.width, y: 0, width: 35, height: 35, 
        dx: -(speedBase * gameSpeed), dy: 0, type: type, angle: 0 
    }};
    
    if (type === 'ground' || type === 'hard') {{
        const gY = getGroundYAtX(enemy.x);
        if (gY !== null) {{
            enemy.y = gY - enemy.height;
        }} else {{
            enemy.type = 'flying';
            enemy.y = Math.random() * 80 + 200;
        }}
    }} else {{
        enemy.y = Math.random() * 80 + 200;
    }}
    enemies.push(enemy);
    let spawnRate = Math.max(20, 60 - (level * 5)); 
    nextEnemySpawn = frameCount + Math.random() * spawnRate + spawnRate;
  }}

  function spawnItem() {{
    items.push({{ x: canvas.width, y: Math.random() * 150 + 150, width: 30, height: 30, dx: -2 }});
    nextItemSpawn = frameCount + Math.random() * 60 + 40;
  }}
  
  function initClouds() {{
    clouds = [];
    for(let i=0; i<5; i++) clouds.push({{x: Math.random() * canvas.width, y: Math.random() * 150, speed: Math.random() * 0.5 + 0.2}});
  }}

  function updateClouds() {{
    for(let c of clouds) {{
        c.x -= c.speed;
        if(c.x < -100) {{ c.x = canvas.width; c.y = Math.random() * 150; }}
    }}
  }}

  function updateLevel() {{
    const newLevel = Math.floor(score / 500) + 1;
    if (newLevel > level) {{
        level = newLevel;
        gameSpeed = 1.0 + (level * 0.1);
        levelEl.innerText = level;
        if(hp < 3) {{ hp++; updateHearts(); }}
        playSound('coin'); 
    }}
  }}

  function updateHearts() {{
    let h = ""; 
    for(let i=0; i<hp; i++) h += "❤️"; 
    heartsEl.innerText = h;
  }}

  function resetGame() {{
    player.x = 100; player.y = 0; player.dx = 0; player.dy = 0;
    score = 0; level = 1; gameSpeed = 1.0; hp = 3;
    enemies = []; items = []; gameOver = false; frameCount = 0;
    isInvincible = false; nextEnemySpawn = 50; nextItemSpawn = 30;
    scoreEl.innerText = score; levelEl.innerText = level;
    updateHearts();
    initClouds();
    generateCourse();

    const startGround = getGroundYUnderPlayer();
    const gY = startGround !== null ? startGround : BASE_GROUND_Y;
    player.y = gY - player.height;

    overlay.style.display = 'none';
    loop();
  }}

  function update() {{
    if (gameOver) return;
    frameCount++;
    updateClouds();
    
    if (isInvincible) {{ 
        invincibleTimer--; 
        if (invincibleTimer <= 0) isInvincible = false; 
    }}

    if (keys.right) player.dx = player.speed;
    else if (keys.left) player.dx = -player.speed;
    else player.dx *= FRICTION;

    player.x += player.dx; 
    player.y += player.dy; 
    player.dy += GRAVITY;

    if (player.x < 0) player.x = 0;
    if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

    const groundY = getGroundYUnderPlayer();
    if (groundY !== null) {{
        if (player.y + player.height >= groundY && player.dy >= 0) {{
            player.y = groundY - player.height;
            player.dy = 0;
            player.jumping = false;
        }}
    }} else {{
        if (player.y > canvas.height) {{
            if (!gameOver) {{
                hp = 0;
                updateHearts();
                playSound('hit');
                handleGameOver();
            }}
        }}
    }}

    if (frameCount >= nextEnemySpawn) spawnEnemy();
    if (frameCount >= nextItemSpawn) spawnItem();

    for (let i = 0; i < items.length; i++) {{
      let item = items[i]; 
      item.x += item.dx;
      if (item.x + item.width < 0) {{ items.splice(i, 1); i--; continue; }}
      if (player.x < item.x + item.width && player.x + player.width > item.x && player.y < item.y + item.height && player.y + player.height > item.y) {{
        score += 50; scoreEl.innerText = score; items.splice(i, 1); i--;
        playSound('coin'); updateLevel();
      }}
    }}

    for (let i = 0; i < enemies.length; i++) {{
      let e = enemies[i]; 
      e.x += e.dx;
      if (e.type === 'flying') {{ e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }}
      if (e.x + e.width < 0) {{ enemies.splice(i, 1); i--; continue; }}

      if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {{
        if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {{
          enemies.splice(i, 1); i--; player.dy = -10; score += 100; scoreEl.innerText = score; playSound('coin'); updateLevel();
        }} else {{
          if (!isInvincible) {{
              hp--; if (hp < 0) hp = 0; updateHearts(); playSound('hit');
              if (hp <= 0) handleGameOver();
              else {{ isInvincible = true; invincibleTimer = 60; enemies.splice(i, 1); i--; }}
          }}
        }}
      }}
    }}
  }}

  function drawObj(img, x, y, w, h, fallbackColor) {{
    if (img.complete && img.naturalHeight !== 0) ctx.drawImage(img, x, y, w, h);
    else {{ ctx.fillStyle = fallbackColor; ctx.fillRect(x, y, w, h); }}
  }}

  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#87CEEB'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    for(let c of clouds) {{ 
        ctx.beginPath(); ctx.arc(c.x, c.y, 30, 0, Math.PI * 2); 
        ctx.arc(c.x + 25, c.y - 10, 35, 0, Math.PI * 2); 
        ctx.arc(c.x + 50, c.y, 30, 0, Math.PI * 2); ctx.fill(); 
    }}
      
    for (let seg of terrainSegments) {{
        ctx.fillStyle = '#654321'; ctx.fillRect(seg.x, seg.topY, seg.width, canvas.height - seg.topY);
        ctx.fillStyle = '#228B22'; ctx.fillRect(seg.x, seg.topY, seg.width, 10);
    }}

    for (let item of items) drawObj(itemImg, item.x, item.y, item.width, item.height, 'gold');
    
    for (let e of enemies) {{
        if (e.type === 'hard') drawObj(enemy2Img, e.x, e.y, e.width, e.height, 'purple');
        else drawObj(enemyImg, e.x, e.y, e.width, e.height, 'red');
    }}

    ctx.save();
    if (isInvincible && Math.floor(Date.now() / 100) % 2 === 0) ctx.globalAlpha = 0.5;
    if (!facingRight) {{ 
        ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); 
        drawObj(playerImg, 0, 0, player.width, player.height, 'blue'); 
    }} else {{ 
        drawObj(playerImg, player.x, player.y, player.width, player.height, 'blue'); 
    }}
    ctx.restore();
  }}

  function loop() {{
    update();
    draw();
    if (!gameOver) requestAnimationFrame(loop);
  }}

  resetGame();

</script>
</body>
</html>
"""

components.html(game_html, height=550, scrolling=False)
