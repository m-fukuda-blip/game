import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json

# ページ設定
st.set_page_config(page_title="Global Ranking Game", layout="wide")
st.title("🎮 修正版：みんなで競うランキング")
st.caption("データはサーバー上のCSVに保存されます（共有ランキング）")

# ==========================================
# 1. Python側：ランキング管理システム (CSV)
# ==========================================
CSV_FILE = 'ranking.csv'

# CSVがなければ作成
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=['name', 'score'])
    df.to_csv(CSV_FILE, index=False)

# URLパラメータからスコアを受け取って保存する処理
# (JSから window.parent.location.href で送られてくる)
qp = st.query_params
if 'new_score' in qp and 'new_name' in qp:
    try:
        new_name = qp['new_name']
        new_score = int(qp['new_score'])
        
        # CSV読み込み
        df = pd.read_csv(CSV_FILE)
        
        # 新しいスコアを追加
        new_row = pd.DataFrame([{'name': new_name, 'score': new_score}])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # ソートしてトップ10を残す
        df = df.sort_values('score', ascending=False).head(10)
        
        # 保存
        df.to_csv(CSV_FILE, index=False)
        
        st.success(f"ランキングを更新しました！ ({new_name}: {new_score})")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
    
    # パラメータをクリアしてリロード（二重送信防止）
    st.query_params.clear()
    # st.rerun() # 必要に応じてコメントアウト解除（自動リロード）

# 最新のランキングを読み込む
df_ranking = pd.read_csv(CSV_FILE)
df_ranking = df_ranking.sort_values('score', ascending=False).head(10)

# JSに渡すためにJSON化
ranking_json = df_ranking.to_json(orient='records')

# ==========================================
# 2. ゲーム本体 (HTML/JS)
# ==========================================
game_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; overflow: hidden; background-color: #222; color: white; font-family: 'Courier New', sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; }}
  canvas {{ background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); image-rendering: pixelated; }}
  #ui-layer {{ position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; pointer-events: none; text-shadow: 1px 1px 0 #fff;}}
  #hearts {{ color: red; font-size: 30px; }}
  
  /* オーバーレイ（入力画面） */
  #overlay {{ 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
    background: rgba(0, 0, 0, 0.9); border: 4px solid white; border-radius: 10px;
    padding: 30px; text-align: center; color: white; display: none; width: 350px;
    z-index: 100;
  }}
  input[type="text"] {{ padding: 10px; font-size: 18px; width: 200px; text-align: center; margin: 10px 0; }}
  button {{ padding: 10px 20px; font-size: 18px; cursor: pointer; background: #f00; color: white; border: none; font-weight: bold; border-radius: 5px; }}
  button:hover {{ background: #ff5555; }}
  .rank-list {{ font-size: 14px; color: #aaa; margin-top: 15px; text-align: left; }}
</style>
</head>
<body>

<div id="ui-layer">
    Score: <span id="score">0</span> | Level: <span id="level">1</span><br>
    Life: <span id="hearts">❤️❤️❤️</span>
</div>

<canvas id="gameCanvas" width="800" height="400"></canvas>

<!-- ゲームオーバー画面 -->
<div id="overlay">
    <h2 style="color:yellow; margin:0;">GAME OVER</h2>
    <p id="final-msg">Score: 0</p>
    
    <!-- ランクイン時のみ表示 -->
    <div id="input-area" style="display:none;">
        <p style="color:cyan; font-weight:bold;">🏆 TOP 10 RANK IN! 🏆</p>
        <input type="text" id="player-name" placeholder="Enter Your Name" maxlength="10">
        <br>
        <button onclick="submitScore()">Save & Restart</button>
    </div>
    
    <!-- ランク外の時のみ表示 -->
    <div id="restart-area" style="display:none;">
        <p>Try again!</p>
        <button onclick="location.reload()">Restart</button>
    </div>
</div>

<script>
  // Pythonから渡されたランキングデータ (JSON文字列として埋め込まれる)
  const currentRankings = {ranking_json}; 
  
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  const scoreEl = document.getElementById('score');
  const levelEl = document.getElementById('level');
  const heartsEl = document.getElementById('hearts');
  
  const overlay = document.getElementById('overlay');
  const inputArea = document.getElementById('input-area');
  const restartArea = document.getElementById('restart-area');
  const finalMsg = document.getElementById('final-msg');
  const nameInput = document.getElementById('player-name');

  // 画像
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

  const player = {{ x: 100, y: 300, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false }};
  let enemies = [];
  let items = [];
  let clouds = [];
  const keys = {{ right: false, left: false, up: false }};
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // 音声関数
  function playSound(type) {{
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    if (type === 'jump') {{
        osc.type = 'square'; osc.frequency.setValueAtTime(150, now); osc.frequency.linearRampToValueAtTime(300, now+0.1);
        gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now+0.1); osc.start(now); osc.stop(now+0.1);
    }} else if (type === 'coin') {{
        osc.type = 'sine'; osc.frequency.setValueAtTime(1200, now); osc.frequency.setValueAtTime(1600, now+0.05);
        gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now+0.2); osc.start(now); osc.stop(now+0.2);
    }} else if (type === 'hit') {{
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, now); osc.frequency.linearRampToValueAtTime(50, now+0.3);
        gain.gain.setValueAtTime(0.2, now); gain.gain.exponentialRampToValueAtTime(0.01, now+0.3); osc.start(now); osc.stop(now+0.3);
    }}
  }}

  // 入力操作
  document.addEventListener('keydown', (e) => {{
    if (gameOver) return; // ゲームオーバー時は操作無効
    if (e.code === 'KeyD') {{ keys.right = true; facingRight = true; }}
    if (e.code === 'KeyA') {{ keys.left = true; facingRight = false; }}
    if (e.code === 'KeyW') {{ if (!player.jumping) {{ player.jumping = true; player.dy = -12; playSound('jump'); }} }}
  }});
  document.addEventListener('keyup', (e) => {{
    if (e.code === 'KeyD') keys.right = false;
    if (e.code === 'KeyA') keys.left = false;
  }});

  // ==========================================
  // サーバーへデータを送る関数
  // ==========================================
  function submitScore() {{
    const name = nameInput.value.trim() || "NoName";
    
    // 親ウィンドウ(Streamlit)のURLを取得し、パラメータを追加してリロードさせる
    // これによりPython側で `st.query_params` として受け取れる
    try {{
        const currentUrl = new URL(window.parent.location.href);
        currentUrl.searchParams.set('new_score', score);
        currentUrl.searchParams.set('new_name', name);
        window.parent.location.href = currentUrl.toString();
    }} catch (e) {{
        console.error("URL redirect failed", e);
        alert("スコア送信に失敗しました。");
    }}
  }}

  function checkRankIn() {{
    // まだ10人いない、または最下位よりスコアが高いならランクイン
    if (currentRankings.length < 10) return true;
    const minScore = currentRankings[currentRankings.length - 1].score;
    return score > minScore;
  }}

  function handleGameOver() {{
    gameOver = true;
    overlay.style.display = 'block';
    finalMsg.innerText = "Final Score: " + score;

    if (score > 0 && checkRankIn()) {{
        inputArea.style.display = 'block';
        restartArea.style.display = 'none';
        nameInput.focus();
    }} else {{
        inputArea.style.display = 'none';
        restartArea.style.display = 'block';
    }}
  }}

  // ==========================================
  // ゲームループ系
  // ==========================================
  function spawnEnemy() {{
    const type = Math.random() < 0.5 ? 'ground' : 'flying';
    let speedBase = Math.random() * 3 + 2;
    let enemy = {{ x: canvas.width, y: 0, width: 35, height: 35, dx: -(speedBase * gameSpeed), dy: 0, type: type, angle: 0 }};
    if (type === 'ground') enemy.y = GROUND_Y - enemy.height;
    else enemy.y = Math.random() * 80 + 200;
    enemies.push(enemy);
    let spawnRate = Math.max(20, 60 - (level * 5)); 
    nextEnemySpawn = frameCount + Math.random() * spawnRate + spawnRate;
  }}

  function spawnItem() {{
    items.push({{ x: canvas.width, y: Math.random() * 150 + 150, width: 30, height: 30, dx: -2 }});
    nextItemSpawn = frameCount + Math.random() * 60 + 40;
  }}

  function updateLevel() {{
    const newLevel = Math.floor(score / 500) + 1;
    if (newLevel > level) {{
        level = newLevel; gameSpeed = 1.0 + (level * 0.1); levelEl.innerText = level;
        if(hp < 3) {{ hp++; heartsEl.innerText = "❤️".repeat(hp); }}
        playSound('coin'); 
    }}
  }}

  function update() {{
    if (gameOver) return;
    frameCount++;
    
    // 雲
    if (clouds.length < 5 && Math.random() < 0.02) clouds.push({{x: canvas.width, y: Math.random()*150, speed: Math.random()*0.5+0.2}});
    for(let i=0; i<clouds.length; i++) {{
        clouds[i].x -= clouds[i].speed;
        if(clouds[i].x < -100) {{ clouds.splice(i, 1); i--; }}
    }}

    if (isInvincible) {{ invincibleTimer--; if (invincibleTimer <= 0) isInvincible = false; }}

    // プレイヤー
    if (keys.right) player.dx = player.speed;
    else if (keys.left) player.dx = -player.speed;
    else player.dx *= FRICTION;
    player.x += player.dx; player.y += player.dy; player.dy += GRAVITY;
    if (player.y + player.height > GROUND_Y) {{ player.y = GROUND_Y - player.height; player.dy = 0; player.jumping = false; }}
    if (player.x < 0) player.x = 0;
    if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

    if (frameCount >= nextEnemySpawn) spawnEnemy();
    if (frameCount >= nextItemSpawn) spawnItem();

    // アイテム
    for (let i = 0; i < items.length; i++) {{
      let item = items[i]; item.x += item.dx;
      if (item.x + item.width < 0) {{ items.splice(i, 1); i--; continue; }}
      if (player.x < item.x + item.width && player.x + player.width > item.x && player.y < item.y + item.height && player.y + player.height > item.y) {{
        score += 50; scoreEl.innerText = score; items.splice(i, 1); i--; playSound('coin'); updateLevel();
      }}
    }}

    // 敵
    for (let i = 0; i < enemies.length; i++) {{
      let e = enemies[i]; e.x += e.dx;
      if (e.type === 'flying') {{ e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }}
      if (e.x + e.width < 0) {{ enemies.splice(i, 1); i--; continue; }}
      if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {{
        if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {{
          enemies.splice(i, 1); i--; player.dy = -10; score += 100; scoreEl.innerText = score; playSound('coin'); updateLevel();
        }} else {{
          if (!isInvincible) {{
              hp--; heartsEl.innerText = "❤️".repeat(hp); playSound('hit');
              if (hp <= 0) handleGameOver();
              else {{ isInvincible = true; invincibleTimer = 60; enemies.splice(i, 1); i--; }}
          }}
        }}
      }}
    }}
  }}

  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#87CEEB'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    for(let c of clouds) {{ ctx.beginPath(); ctx.arc(c.x, c.y, 30, 0, Math.PI * 2); ctx.arc(c.x + 25, c.y - 10, 35, 0, Math.PI * 2); ctx.arc(c.x + 50, c.y, 30, 0, Math.PI * 2); ctx.fill(); }}
     
    ctx.fillStyle = '#654321'; ctx.fillRect(0, GROUND_Y, canvas.width, 40);
    ctx.fillStyle = '#228B22'; ctx.fillRect(0, GROUND_Y, canvas.width, 10);

    for (let item of items) {{ if (itemImg.complete) ctx.drawImage(itemImg, item.x, item.y, item.width, item.height); else {{ ctx.fillStyle='gold'; ctx.fillRect(item.x,item.y,item.width,item.height); }} }}
    for (let e of enemies) {{ if (enemyImg.complete) ctx.drawImage(enemyImg, e.x, e.y, e.width, e.height); else {{ ctx.fillStyle='red'; ctx.fillRect(e.x,e.y,e.width,e.height); }} }}

    ctx.save();
    if (isInvincible && Math.floor(Date.now() / 100) % 2 === 0) ctx.globalAlpha = 0.5;
    if (!facingRight) {{ ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); if (playerImg.complete) ctx.drawImage(playerImg, 0, 0, player.width, player.height); else {{ ctx.fillStyle='blue'; ctx.fillRect(0,0,player.width,player.height); }} }} 
    else {{ if (playerImg.complete) ctx.drawImage(playerImg, player.x, player.y, player.width, player.height); else {{ ctx.fillStyle='blue'; ctx.fillRect(player.x,player.y,player.width,player.height); }} }}
    ctx.restore();
  }}

  function loop() {{
    update();
    draw();
    if (!gameOver) requestAnimationFrame(loop);
  }}
  
  loop();
</script>
</body>
</html>
"""

# ゲームを表示
components.html(game_html, height=500)

# ランキング表を表示 (Python側)
st.markdown("### 🏆 Global Ranking (Top 10)")
st.table(df_ranking)
