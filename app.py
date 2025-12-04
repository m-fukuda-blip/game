import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Game with Ranking & Animation", layout="wide")
st.title("🎮 アクションゲーム：アニメーション実装版")
st.caption("機能：❤️ライフ制 / 🆙レベルアップ / ☁️背景 / 🔊効果音 / 🏆グローバルランキング / 🏃‍♂️キャラクターアニメーション")
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
    
    <!-- 名前入力エリア -->
    <div id="input-section">
        <p style="color: cyan;">🎉 NEW RECORD! 🎉</p>
        <input type="text" id="player-name" placeholder="Enter Name" maxlength="8">
        <button id="submit-btn" onclick="submitScore()">Save</button>
        <div id="loading-msg">⏳ Saving to Global Ranking...</div>
    </div>

    <!-- ランキング表 -->
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

  // ==========================================
  // ★ アニメーション画像の読み込み
  // ==========================================
  // ⚠️注意⚠️ 以下のURLをご自身の画像URLに書き換えてください！
  const playerAnim = {{
      idle: [],
      run: [],
      jump: [],
      dead: null
  }};
  
  // 待機 (Taiki01 ~ 03)
  for(let i=1; i<=3; i++) {{ let img = new Image(); img.src = `https://example.com/Taiki0${{i}}.png`; playerAnim.idle.push(img); }}
  // 走り (Run01 ~ 03)
  for(let i=1; i<=3; i++) {{ let img = new Image(); img.src = `https://example.com/Run0${{i}}.png`; playerAnim.run.push(img); }}
  // ジャンプ (Jump01 ~ 03)
  for(let i=1; i<=3; i++) {{ let img = new Image(); img.src = `https://example.com/Jump0${{i}}.png`; playerAnim.jump.push(img); }}
  // 死亡 (Dead)
  playerAnim.dead = new Image(); playerAnim.dead.src = "https://example.com/Dead.png";

  // その他の画像（変更なし）
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
  
  // ★ プレイヤーオブジェクトにアニメーション情報を追加
  const player = {{ 
      x: 100, y: 0, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false,
      state: 'idle',       // idle, running, jumping, dead
      animIndex: 0,        // 現在のアニメーションフレーム
      animTimer: 0,        // フレーム切り替えタイマー
      animSpeedIdle: 15,   // 待機アニメの速度（大きいほど遅い）
      animSpeedRun: 8,     // 走りアニメの速度
      idlePingPong: 1      // 待機の往復用 (1 or -1)
  }};
  
  let enemies = [];
  let items = [];
  let clouds = [];
  const keys = {{ right: false, left: false, up: false }};

  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // ==========================================
  // API設定 (GAS) - 変更なし
  // ==========================================
  const API_URL = "{GAS_API_URL}";
  let globalRankings = [];

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

  fetchRankings().then(data => {{ globalRankings = data; }});

  function checkRankIn(currentScore) {{
    if (globalRankings.length < 10) return true;
    return currentScore > globalRankings[globalRankings.length - 1].score;
  }}

  async function submitScore() {{
    const name = nameInput.value.trim() || "NO NAME";
    nameInput.disabled = true;
    submitBtn.disabled = true;
    loadingMsg.style.display = 'block';
    
    await sendScore(name, score);
    globalRankings = await fetchRankings();
    
    loadingMsg.style.display = 'none';
    nameInput.disabled = false;
    submitBtn.disabled = false;
    inputSection.style.display = 'none';
    showRankingTable(globalRankings);
  }}

  function showRankingTable(rankings) {{
    if (!rankings) rankings = globalRankings;
    rankingBody.innerHTML = "";
    for (let i = 0; i < 10; i++) {{
        let r = rankings[i];
        let row = document.createElement('tr');
        if (r) {{
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
    // ★死亡状態にセット
    player.state = 'dead'; 
    overlay.style.display = 'block';
    finalScoreDisplay.innerText = "Final Score: " + score;
    nameInput.value = "";
    rankingBody.innerHTML = ""; 
    rankLoading.style.display = "block";

    fetchRankings().then(data => {{
        globalRankings = data;
        rankLoading.style.display = "none";
        showRankingTable(globalRankings);
        if (score > 0 && checkRankIn(score)) {{
            inputSection.style.display = 'block';
            nameInput.focus();
        }} else {{
            inputSection.style.display = 'none';
        }}
    }});
  }}

  // ==========================================
  // ゲームロジック
  // ==========================================
  
  function playSound(type) {{
    // 省略（変更なし）
  }}

  document.addEventListener('keydown', (e) => {{
    if (document.activeElement === nameInput) {{
        if (e.key === 'Enter' && !submitBtn.disabled) submitScore();
        return;
    }}
    // ★死亡時は操作を受け付けない
    if (player.state === 'dead' && e.code !== 'KeyR') return;

    if (['KeyW', 'KeyA', 'KeyD', 'KeyR'].includes(e.code)) {{ e.preventDefault(); }}
    if (e.code === 'KeyD') {{ keys.right = true; facingRight = true; }}
    if (e.code === 'KeyA') {{ keys.left = true; facingRight = false; }}
    if (e.code === 'KeyW') {{ 
        if (!player.jumping && !gameOver) {{ 
            player.jumping = true; 
            player.dy = -12; 
            // playSound('jump'); // 音は一旦OFF
        }} 
    }}
    if (e.code === 'KeyR' && gameOver) resetGame();
  }});

  document.addEventListener('keyup', (e) => {{
    if (e.code === 'KeyD') keys.right = false;
    if (e.code === 'KeyA') keys.left = false;
  }});

  // generateCourse, getGroundYUnderPlayer, getGroundYAtX, spawnEnemy, spawnItem, initClouds, updateClouds, updateLevel
  // などの関数は変更なしのため省略（元のコードを維持）
  function generateCourse() {{
    terrainSegments = [];
    let x = 0; let prevLevel = 0; const SEG_HEIGHTS = [BASE_GROUND_Y, BASE_GROUND_Y - 40, BASE_GROUND_Y - 80];
    while (x < canvas.width + 100) {{
        let width = Math.random() * 120 + 80; let gapWidth = 0;
        if (x > 250 && Math.random() < 0.25) gapWidth = Math.random() * 80 + 60;
        x += gapWidth;
        let delta = Math.floor(Math.random() * 3) - 1; let newLevel = Math.min(2, Math.max(0, prevLevel + delta));
        prevLevel = newLevel; terrainSegments.push({{ x: x, width: width, topY: SEG_HEIGHTS[newLevel] }});
        x += width;
    }}
  }}
  function getGroundYUnderPlayer() {{
    let groundY = null;
    for (let seg of terrainSegments) {{ if (player.x + player.width > seg.x && player.x < seg.x + seg.width) {{ if (groundY === null || seg.topY < groundY) groundY = seg.topY; }} }}
    return groundY;
  }}
  function getGroundYAtX(x) {{
    let groundY = null;
    for (let seg of terrainSegments) {{ if (x >= seg.x && x <= seg.x + seg.width) {{ if (groundY === null || seg.topY < groundY) groundY = seg.topY; }} }}
    return groundY;
  }}
  function spawnEnemy() {{
    let type = Math.random() < 0.5 ? 'ground' : 'flying'; let speedBase = Math.random() * 3 + 2;
    if (score >= 2000 && Math.random() < 0.3) {{ type = 'hard'; speedBase = 7; }}
    let enemy = {{ x: canvas.width, y: 0, width: 35, height: 35, dx: -(speedBase * gameSpeed), dy: 0, type: type, angle: 0 }};
    if (type === 'ground' || type === 'hard') {{ const gY = getGroundYAtX(enemy.x); if (gY !== null) enemy.y = gY - enemy.height; else {{ enemy.type = 'flying'; enemy.y = Math.random() * 80 + 200; }} }} else enemy.y = Math.random() * 80 + 200;
    enemies.push(enemy); nextEnemySpawn = frameCount + Math.random() * (Math.max(20, 60 - (level * 5))) + Math.max(20, 60 - (level * 5));
  }}
  function spawnItem() {{ items.push({{ x: canvas.width, y: Math.random() * 150 + 150, width: 30, height: 30, dx: -2 }}); nextItemSpawn = frameCount + Math.random() * 60 + 40; }}
  function initClouds() {{ clouds = []; for(let i=0; i<5; i++) clouds.push({{x: Math.random() * canvas.width, y: Math.random() * 150, speed: Math.random() * 0.5 + 0.2}}); }}
  function updateClouds() {{ for(let c of clouds) {{ c.x -= c.speed; if(c.x < -100) {{ c.x = canvas.width; c.y = Math.random() * 150; }} }} }}
  function updateLevel() {{ const newLevel = Math.floor(score / 500) + 1; if (newLevel > level) {{ level = newLevel; gameSpeed = 1.0 + (level * 0.1); levelEl.innerText = level; if(hp < 3) {{ hp++; updateHearts(); }} }} }}


  function updateHearts() {{
    let h = ""; for(let i=0; i<hp; i++) h += "❤️"; heartsEl.innerText = h;
  }}

  function resetGame() {{
    player.x = 100; player.y = 0; player.dx = 0; player.dy = 0;
    // ★初期状態をセット
    player.state = 'idle'; player.animIndex = 0; player.animTimer = 0; player.idlePingPong = 1;
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

  // ==========================================
  // ★ アニメーション更新ロジック
  // ==========================================
  function updatePlayerAnimation() {{
    // 1. 状態の決定
    if (hp <= 0) {{
        player.state = 'dead';
    }} else if (player.jumping) {{
        player.state = 'jumping';
    }} else if (keys.right || keys.left) {{
        player.state = 'running';
    }} else {{
        player.state = 'idle';
    }}

    // 2. 状態ごとのフレーム更新
    player.animTimer++;

    switch (player.state) {{
        case 'idle':
            // Taiki01 -> 02 -> 03 -> 02 -> 01 の往復ループ
            if (player.animTimer > player.animSpeedIdle) {{
                player.animIndex += player.idlePingPong;
                if (player.animIndex >= 2) player.idlePingPong = -1; // 03まで行ったら折り返し
                if (player.animIndex <= 0) player.idlePingPong = 1;  // 01まで戻ったら折り返し
                player.animTimer = 0;
            }}
            break;
            
        case 'running':
            // Run01 -> 02 -> 03 -> 01 のループ
            if (player.animTimer > player.animSpeedRun) {{
                player.animIndex = (player.animIndex + 1) % 3;
                player.animTimer = 0;
            }}
            break;
            
        case 'jumping':
            // 上昇速度(dy)に応じてフレームを切り替える（自然な見た目にするため）
            if (player.dy < -5) {{
                player.animIndex = 0; // Jump01: 上昇開始（勢いよく）
            }} else if (player.dy < 0) {{
                player.animIndex = 1; // Jump02: 上昇中（ふわっと）
            }} else if (player.dy < 5) {{
                player.animIndex = 2; // Jump03: 最高点付近
            }} else {{
                player.animIndex = 1; // Jump02: 下降中（ふわっと）
            }}
            // 着地(Taiki01)は、stateがidle/runningに戻ることで自然に表現される
            break;
            
        case 'dead':
            player.animIndex = 0; // Dead画像に固定
            break;
    }}
  }}

  function update() {{
    if (gameOver && player.state !== 'dead') return; // 死亡アニメ中は少し動かすかも
    if (player.state === 'dead') return; // 完全に停止

    frameCount++;
    updateClouds();
    if (isInvincible) {{ invincibleTimer--; if (invincibleTimer <= 0) isInvincible = false; }}

    // ★移動入力（死亡時は無効）
    if (player.state !== 'dead') {{
        if (keys.right) player.dx = player.speed;
        else if (keys.left) player.dx = -player.speed;
        else player.dx *= FRICTION;
    }}

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
                // playSound('hit');
                handleGameOver();
            }}
        }}
    }}
    
    // ★アニメーションを更新
    updatePlayerAnimation();

    if (gameOver) return; // ゲームオーバーなら敵・アイテムの更新はしない

    // 敵・アイテム生成と更新処理（省略・変更なし）
    if (frameCount >= nextEnemySpawn) spawnEnemy();
    if (frameCount >= nextItemSpawn) spawnItem();
    for (let i = 0; i < items.length; i++) {{ let item = items[i]; item.x += item.dx; if (item.x + item.width < 0) {{ items.splice(i, 1); i--; continue; }} if (player.x < item.x + item.width && player.x + player.width > item.x && player.y < item.y + item.height && player.y + player.height > item.y) {{ score += 50; scoreEl.innerText = score; items.splice(i, 1); i--; updateLevel(); }} }}
    for (let i = 0; i < enemies.length; i++) {{ let e = enemies[i]; e.x += e.dx; if (e.type === 'flying') {{ e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }} if (e.x + e.width < 0) {{ enemies.splice(i, 1); i--; continue; }} if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {{ if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {{ enemies.splice(i, 1); i--; player.dy = -10; score += 100; scoreEl.innerText = score; updateLevel(); }} else {{ if (!isInvincible) {{ hp--; if (hp < 0) hp = 0; updateHearts(); if (hp <= 0) handleGameOver(); else {{ isInvincible = true; invincibleTimer = 60; enemies.splice(i, 1); i--; }} }} }} }} }}
  }}

  function drawObj(img, x, y, w, h, fallbackColor) {{
    if (img && img.complete && img.naturalHeight !== 0) ctx.drawImage(img, x, y, w, h);
    else {{ ctx.fillStyle = fallbackColor; ctx.fillRect(x, y, w, h); }}
  }}

  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#87CEEB'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 雲、地形、アイテム、敵の描画（変更なし）
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'; for(let c of clouds) {{ ctx.beginPath(); ctx.arc(c.x, c.y, 30, 0, Math.PI * 2); ctx.arc(c.x + 25, c.y - 10, 35, 0, Math.PI * 2); ctx.arc(c.x + 50, c.y, 30, 0, Math.PI * 2); ctx.fill(); }}
    for (let seg of terrainSegments) {{ ctx.fillStyle = '#654321'; ctx.fillRect(seg.x, seg.topY, seg.width, canvas.height - seg.topY); ctx.fillStyle = '#228B22'; ctx.fillRect(seg.x, seg.topY, seg.width, 10); }}
    for (let item of items) drawObj(itemImg, item.x, item.y, item.width, item.height, 'gold');
    for (let e of enemies) {{ if (e.type === 'hard') drawObj(enemy2Img, e.x, e.y, e.width, e.height, 'purple'); else drawObj(enemyImg, e.x, e.y, e.width, e.height, 'red'); }}

    // ★ プレイヤーの描画（アニメーション対応）
    ctx.save();
    if (isInvincible && Math.floor(Date.now() / 100) % 2 === 0) ctx.globalAlpha = 0.5;
    
    // 現在の状態に応じた画像を選択
    let currentImg = null;
    if (player.state === 'dead') {{
        currentImg = playerAnim.dead;
    }} else {{
        // idle, running, jumping は配列から選択
        currentImg = playerAnim[player.state][player.animIndex];
    }}

    // 左右反転処理と描画
    if (!facingRight) {{ 
        ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); 
        drawObj(currentImg, 0, 0, player.width, player.height, 'blue'); 
    }} else {{ 
        drawObj(currentImg, player.x, player.y, player.width, player.height, 'blue'); 
    }}
    ctx.restore();
  }}

  function loop() {{
    update();
    draw();
    // 死亡状態でも描画を続けるためにループは止めない（updateで制御）
    requestAnimationFrame(loop);
  }}

  resetGame();

</script>
</body>
</html>
"""

components.html(game_html, height=550, scrolling=False)
