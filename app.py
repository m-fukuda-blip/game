import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from github import Github

# ==========================================
# ⚙️ 設定エリア (ここだけ書き換えてください！)
# ==========================================
APP_URL = "https://379e3dtthewydkexmys3au.streamlit.app/" 
# ↑ あなたのアプリURLに変更

st.set_page_config(page_title="Gist Ranking Game", layout="wide")
st.title("🏆 GitHub Gist ランキング (修正版)")
st.caption("音の修正 & 読み込みエラー修正済み")

# ==========================================
# GitHub Gist 連携処理 (ファイル名無視の最強版)
# ==========================================
def get_ranking_from_gist():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        gist_id = st.secrets["GIST_ID"]
        
        g = Github(token)
        gist = g.get_gist(gist_id)
        
        # ファイル名が何であっても「1つ目のファイル」を取得する
        if not gist.files:
            return []
        
        file_name = list(gist.files.keys())[0] 
        file = gist.files[file_name]
        content = file.content
        
        if not content or content == "{}": 
            return []
            
        data = json.loads(content)
        return data
    except Exception as e:
        # デバッグ用にエラーを表示しない（空リストとして扱う）
        # print(f"Error: {e}") 
        return []

def save_ranking_to_gist(new_data):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        gist_id = st.secrets["GIST_ID"]
        
        g = Github(token)
        gist = g.get_gist(gist_id)
        
        # 保存するときも「1つ目のファイル」に書き込む
        file_name = list(gist.files.keys())[0]
        
        gist.edit(files={file_name: {"content": json.dumps(new_data)}})
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

# ==========================================
# ランキング更新ロジック
# ==========================================
current_data = get_ranking_from_gist()

# リスト形式でない場合（初回など）のケア
if not isinstance(current_data, list):
    current_data = []

qp = st.query_params
if 'new_score' in qp and 'new_name' in qp:
    new_name = qp['new_name']
    new_score = int(qp['new_score'])
    
    current_data.append({"name": new_name, "score": new_score})
    # スコア順にソート
    current_data = sorted(current_data, key=lambda x: x['score'], reverse=True)[:10]
    
    if save_ranking_to_gist(current_data):
        st.toast(f"🎉 ランキング更新！ {new_name}: {new_score}")
    
    st.query_params.clear()

df_ranking = pd.DataFrame(current_data)
if not df_ranking.empty:
    if 'score' in df_ranking.columns:
        df_ranking = df_ranking.sort_values('score', ascending=False).reset_index(drop=True)
        df_ranking.index += 1
    ranking_json = df_ranking.to_json(orient='records')
else:
    ranking_json = "[]"
    df_ranking = pd.DataFrame(columns=["name", "score"])

# ==========================================
# ゲーム本体 (HTML/JS) - 音修正済み
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
  
  #overlay {{ 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
    background: rgba(0, 0, 0, 0.9); border: 4px solid white; border-radius: 10px;
    padding: 30px; text-align: center; color: white; display: none; width: 350px;
    z-index: 100;
  }}
  input[type="text"] {{ padding: 10px; font-size: 18px; width: 200px; text-align: center; margin: 10px 0; }}
  button {{ padding: 10px 20px; font-size: 18px; cursor: pointer; background: #f00; color: white; border: none; font-weight: bold; border-radius: 5px; }}
  button:hover {{ background: #ff5555; }}
</style>
</head>
<body>

<div id="ui-layer">
    Score: <span id="score">0</span> | Level: <span id="level">1</span><br>
    Life: <span id="hearts">❤️❤️❤️</span>
</div>

<canvas id="gameCanvas" width="800" height="400"></canvas>

<div id="overlay">
    <h2 style="color:yellow; margin:0;">GAME OVER</h2>
    <p id="final-msg">Score: 0</p>
    
    <div id="input-area" style="display:none;">
        <p style="color:cyan; font-weight:bold;">🏆 TOP 10 RANK IN! 🏆</p>
        <input type="text" id="player-name" placeholder="Enter Your Name" maxlength="10">
        <br>
        <button onclick="submitScore()">Save & Restart</button>
    </div>
    
    <div id="restart-area" style="display:none;">
        <p>Try again!</p>
        <button onclick="reloadGame()">Restart</button>
    </div>
</div>

<script>
  const currentRankings = {ranking_json}; 
  const appUrl = "{APP_URL}";

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

  const playerImg = new Image(); playerImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/player.png";
  const enemyImg = new Image(); enemyImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/enemy.png";
  const itemImg = new Image(); itemImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png";

  const GRAVITY = 0.6; const FRICTION = 0.8; const GROUND_Y = 360;
  let score = 0; level = 1; gameSpeed = 1.0; hp = 3;
  let gameOver = false; frameCount = 0;
  let nextEnemySpawn = 0; nextItemSpawn = 0;
  let facingRight = true; isInvincible = false; invincibleTimer = 0;

  const player = {{ x: 100, y: 300, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false }};
  let enemies = []; items = []; clouds = [];
  const keys = {{ right: false, left: false, up: false }};
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // 🔊 ここで音色 (osc.type) を復活させました！
  function playSound(type) {{
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator(); 
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    
    if (type === 'jump') {{ 
        osc.type = 'square'; // 復活：ピコッ！
        osc.frequency.setValueAtTime(150, now); 
        osc.frequency.linearRampToValueAtTime(300, now+0.1); 
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now+0.1); 
        osc.start(now); osc.stop(now+0.1); 
    }}
    else if (type === 'coin') {{ 
        osc.type = 'sine'; // 復活：キラリン
        osc.frequency.setValueAtTime(1200, now); 
        osc.frequency.setValueAtTime(1600, now+0.05);
        gain.gain.setValueAtTime(0.1, now); 
        gain.gain.exponentialRampToValueAtTime(0.01, now+0.2); 
        osc.start(now); osc.stop(now+0.2); 
    }}
    else if (type === 'hit') {{ 
        osc.type = 'sawtooth'; // 復活：ビビビ！
        osc.frequency.setValueAtTime(100, now); 
        osc.frequency.linearRampToValueAtTime(50, now+0.3);
        gain.gain.setValueAtTime(0.2, now); 
        gain.gain.exponentialRampToValueAtTime(0.01, now+0.3); 
        osc.start(now); osc.stop(now+0.3); 
    }}
  }}

  document.addEventListener('keydown', (e) => {{
    if (gameOver) return; 
    if (e.code === 'KeyD') {{ keys.right = true; facingRight = true; }}
    if (e.code === 'KeyA') {{ keys.left = true; facingRight = false; }}
    if (e.code === 'KeyW' && !player.jumping) {{ player.jumping = true; player.dy = -12; playSound('jump'); }}
  }});
  document.addEventListener('keyup', (e) => {{ if (e.code === 'KeyD') keys.right = false; if (e.code === 'KeyA') keys.left = false; }});

  function submitScore() {{
    const name = nameInput.value.trim() || "NoName";
    const targetUrl = new URL(appUrl);
    targetUrl.searchParams.set('new_score', score);
    targetUrl.searchParams.set('new_name', name);
    const link = document.createElement('a');
    link.href = targetUrl.toString();
    link.target = "_top";
    document.body.appendChild(link);
    link.click();
  }}
  
  function reloadGame() {{
    const link = document.createElement('a'); link.href = appUrl; link.target = "_top"; document.body.appendChild(link); link.click();
  }}

  function checkRankIn() {{
    // ランキングが空、または10人未満なら絶対ランクイン
    if (!currentRankings || currentRankings.length < 10) return true;
    const minScore = currentRankings[currentRankings.length - 1].score;
    return score > minScore;
  }}

  function handleGameOver() {{
    gameOver = true; overlay.style.display = 'block'; finalMsg.innerText = "Final Score: " + score;
    if (score > 0 && checkRankIn()) {{ inputArea.style.display = 'block'; restartArea.style.display = 'none'; nameInput.focus(); }} 
    else {{ inputArea.style.display = 'none'; restartArea.style.display = 'block'; }}
  }}

  function spawnEnemy() {{
    const type = Math.random() < 0.5 ? 'ground' : 'flying';
    let e = {{ x: canvas.width, y: 0, width: 35, height: 35, dx: -(Math.random()*3+2)*gameSpeed, dy: 0, type: type, angle: 0 }};
    if (type === 'ground') e.y = GROUND_Y - e.height; else e.y = Math.random() * 80 + 200;
    enemies.push(e);
    nextEnemySpawn = frameCount + Math.random()*60 + Math.max(20, 60-(level*5));
  }}

  function update() {{
    if (gameOver) return;
    frameCount++;
    if (Math.random()<0.02 && clouds.length<5) clouds.push({{x:canvas.width, y:Math.random()*150, s:Math.random()*0.5+0.2}});
    clouds.forEach(c => c.x -= c.s);
    if (isInvincible) {{ invincibleTimer--; if (invincibleTimer<=0) isInvincible=false; }}

    if (keys.right) player.dx = player.speed; else if (keys.left) player.dx = -player.speed; else player.dx *= FRICTION;
    player.x += player.dx; player.y += player.dy; player.dy += GRAVITY;
    if (player.y+player.height > GROUND_Y) {{ player.y=GROUND_Y-player.height; player.dy=0; player.jumping=false; }}
    if (player.x < 0) player.x = 0; if (player.x > canvas.width-player.width) player.x = canvas.width-player.width;

    if (frameCount >= nextEnemySpawn) spawnEnemy();
    if (frameCount >= nextItemSpawn) {{ items.push({{x:canvas.width, y:Math.random()*150+150, w:30, h:30, dx:-2}}); nextItemSpawn = frameCount+Math.random()*60+40; }}

    for (let i=0; i<items.length; i++) {{
      items[i].x += items[i].dx;
      if (items[i].x < -50) {{ items.splice(i,1); i--; continue; }}
      if (player.x < items[i].x + items[i].width && player.x + player.width > items[i].x && player.y < items[i].y + items[i].height && player.y + player.height > items[i].y) {{
        score+=50; scoreEl.innerText=score; items.splice(i,1); i--; playSound('coin');
        const newLvl = Math.floor(score/500)+1;
        if (newLvl > level) {{ level=newLvl; gameSpeed=1.0+(level*0.1); levelEl.innerText=level; if(hp<3){{hp++; heartsEl.innerText="❤️".repeat(hp);}} playSound('coin'); }}
      }}
    }}

    for (let i=0; i<enemies.length; i++) {{
      let e = enemies[i]; e.x += e.dx;
      if (e.type==='flying') {{ e.angle+=0.1; e.y+=Math.sin(e.angle)*2; }}
      if (e.x < -50) {{ enemies.splice(i,1); i--; continue; }}
      if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {{
        if (player.dy > 0 && player.y+player.height < e.y+e.height*0.6) {{
            enemies.splice(i,1); i--; player.dy=-10; score+=100; scoreEl.innerText=score; playSound('coin');
            const newLvl = Math.floor(score/500)+1;
            if (newLvl > level) {{ level=newLvl; gameSpeed=1.0+(level*0.1); levelEl.innerText=level; if(hp<3){{hp++; heartsEl.innerText="❤️".repeat(hp);}} playSound('coin'); }}
        }} else if (!isInvincible) {{
            hp--; heartsEl.innerText="❤️".repeat(hp); playSound('hit');
            if (hp<=0) handleGameOver(); else {{ isInvincible=true; invincibleTimer=60; enemies.splice(i,1); i--; }}
        }}
      }}
    }}
  }}

  function draw() {{
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='#87CEEB'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='rgba(255,255,255,0.7)'; clouds.forEach(c => {{ ctx.beginPath(); ctx.arc(c.x,c.y,30,0,Math.PI*2); ctx.fill(); }});
    ctx.fillStyle='#654321'; ctx.fillRect(0,GROUND_Y,canvas.width,40); ctx.fillStyle='#228B22'; ctx.fillRect(0,GROUND_Y,canvas.width,10);
    items.forEach(i => {{ if(itemImg.complete) ctx.drawImage(itemImg, i.x, i.y, i.width, i.height); else {{ctx.fillStyle='gold'; ctx.fillRect(i.x,i.y,i.width,i.height);}} }});
    enemies.forEach(e => {{ if(enemyImg.complete) ctx.drawImage(enemyImg, e.x, e.y, e.width, e.height); else {{ctx.fillStyle='red'; ctx.fillRect(e.x,e.y,e.width,e.height);}} }});
    ctx.save();
    if (isInvincible && Math.floor(Date.now()/100)%2===0) ctx.globalAlpha=0.5;
    if (!facingRight) {{ ctx.translate(player.x+player.width, player.y); ctx.scale(-1,1); if(playerImg.complete) ctx.drawImage(playerImg, 0,0,player.width,player.height); else {{ctx.fillStyle='blue'; ctx.fillRect(0,0,player.width,player.height);}} }}
    else {{ if(playerImg.complete) ctx.drawImage(playerImg, player.x, player.y, player.width, player.height); else {{ctx.fillStyle='blue'; ctx.fillRect(player.x,player.y,player.width,player.height);}} }}
    ctx.restore();
  }}

  function loop() {{ update(); draw(); if (!gameOver) requestAnimationFrame(loop); }}
  setTimeout(loop, 100); 
</script>
</body>
</html>
"""

components.html(game_html, height=500)

st.markdown("### 🏆 Global Ranking (via GitHub Gist)")
st.table(df_ranking)
