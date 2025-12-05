import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Game with Ranking & Animation", layout="wide")

# タイトル画像を表示
st.image("https://raw.githubusercontent.com/m-fukuda-blip/game/main/gametitlefix.png", use_column_width=True)

st.caption("機能：❤️ライフ / 🆙レベル / ☁️背景変化 / 🔊音 / 🏆ランク / 🏃‍♂️アニメ / 🎵BGM / ✨アイテム / 🧗‍♂️段差 / 💥コンボ / 🫨シェイク / 📏サイズ / 🦘2段ジャンプ / ✨撃破演出 / ⬇️しゃがみ / ⏩横スクロール / 🧱空中足場 / ⛩️ゲート / 🗻パララックス背景")
st.write("操作方法: **W** ジャンプ(2回可) / **A** 左移動 / **D** 右移動 / **S** しゃがみ / **R** リセット / **F** 全画面")

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
  body {{ 
    margin: 0; 
    overflow: hidden; 
    background-color: #222; 
    color: white; 
    font-family: 'Courier New', sans-serif; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    height: 80vh;
    
    /* スマホでの誤操作防止 */
    user-select: none;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
    touch-action: none;
  }}
  
  /* Canvas設定 */
  canvas {{ background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
  
  /* --- UIレイヤー --- */
  #ui-layer {{ position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; pointer-events: none; text-shadow: 1px 1px 0 #fff; z-index: 5; }}
  #hearts {{ color: red; font-size: 30px; }}
  #status-msg {{ font-size: 20px; margin-top: 5px; }}

  /* --- タイトル画面 --- */
  #title-screen {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    background: rgba(0,0,0,0.4); z-index: 10;
    pointer-events: none;
  }}
  
  .title-img {{
    max-width: 22%; 
    height: auto; 
    margin-bottom: 20px;
    opacity: 0; 
  }}

  /* スマホ向けタイトル画像サイズ調整 */
  @media (max-width: 800px) {{
    .title-img {{ max-width: 60%; }}
  }}

  .start-text {{
    font-size: 40px; color: white; text-shadow: 2px 2px #000;
    font-weight: bold; opacity: 0;
  }}
  
  /* アニメーション定義 */
  @keyframes slideUpFade {{
    0% {{ opacity: 0; transform: translateY(100px); }}
    100% {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes blinkFade {{
    0% {{ opacity: 0; }}
    100% {{ opacity: 1; }}
  }}

  /* --- ゲームオーバー・ランキング画面 --- */
  #overlay {{ 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
    background: rgba(0, 0, 0, 0.85); border: 4px solid white; border-radius: 10px;
    padding: 30px; text-align: center; color: white; display: none; width: 400px; 
    max-width: 90%; 
    z-index: 200; 
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
  input[type="text"] {{ 
    padding: 5px; font-size: 16px; width: 150px; text-align: center; 
    user-select: text;
    -webkit-user-select: text;
  }}
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

  /* --- モバイルコントローラー --- */
  #mobile-controls {{
    display: none;
    position: absolute;
    bottom: 20px;
    left: 0;
    width: 100%;
    height: 120px; 
    z-index: 100;
    pointer-events: none; 
    justify-content: space-between;
    padding: 0 10px;
    box-sizing: border-box;
  }}

  /* スマホ・タブレット（タッチデバイス）でのみ表示 */
  @media (hover: none) and (pointer: coarse) {{
    #mobile-controls {{ display: flex; }}
    .restart-msg {{ display: none; }}
  }}

  .control-group {{
    pointer-events: auto;
    display: flex;
    gap: 15px;
    align-items: center;
  }}

  .touch-btn {{
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.6);
    color: white;
    font-size: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    touch-action: manipulation;
    user-select: none;
    -webkit-user-select: none;
    cursor: pointer;
    text-shadow: 1px 1px 2px black;
  }}
  .touch-btn:active {{ background: rgba(255, 255, 255, 0.5); }}
  
  /* 自動リスタートメッセージ */
  #auto-restart-msg {{
      display: none;
      color: #00d2ff;
      margin-top: 20px;
      font-size: 18px;
      font-weight: bold;
      animation: blink 1s infinite;
  }}

</style>
</head>
<body>

<!-- UI表示 -->
<div id="ui-layer">
    Score: <span id="score">0</span> | Level: <span id="level">1</span><br>
    Life: <span id="hearts">❤️❤️❤️</span>
    <div id="status-msg"></div>
</div>

<!-- キャンバス -->
<canvas id="gameCanvas" width="800" height="400"></canvas>

<!-- タイトル画面 -->
<div id="title-screen">
    <img id="title-img" class="title-img" src="https://raw.githubusercontent.com/m-fukuda-blip/game/main/game_title.png" alt="GAME TITLE">
    <div id="start-text" class="start-text">GAME START!</div>
</div>

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
    <!-- 自動リスタートメッセージ -->
    <div id="auto-restart-msg"></div>
</div>

<!-- モバイルコントローラー -->
<div id="mobile-controls">
    <div class="control-group">
        <div id="btn-left" class="touch-btn">◀</div>
        <!-- しゃがみボタン -->
        <div id="btn-down" class="touch-btn">▼</div>
        <div id="btn-right" class="touch-btn">▶</div>
    </div>
    <div class="control-group">
        <div id="btn-jump" class="touch-btn" style="background: rgba(255, 200, 0, 0.4);">▲</div>
    </div>
</div>

<script>
  // 右クリックメニュー防止
  document.addEventListener('contextmenu', event => event.preventDefault());

  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  
  // スマホ判定
  const isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (window.innerWidth < 800);

  if (window.innerWidth < 800) {{
      canvas.width = window.innerWidth - 20; 
  }}

  const scoreEl = document.getElementById('score');
  const levelEl = document.getElementById('level');
  const heartsEl = document.getElementById('hearts');
  const statusMsgEl = document.getElementById('status-msg');
  
  const overlay = document.getElementById('overlay');
  const inputSection = document.getElementById('input-section');
  const rankingBody = document.getElementById('ranking-body');
  const finalScoreDisplay = document.getElementById('final-score-display');
  const nameInput = document.getElementById('player-name');
  const submitBtn = document.getElementById('submit-btn');
  const loadingMsg = document.getElementById('loading-msg');
  const rankLoading = document.getElementById('rank-loading');
  const autoRestartMsg = document.getElementById('auto-restart-msg');

  const titleScreen = document.getElementById('title-screen');
  const titleImg = document.getElementById('title-img');
  const startText = document.getElementById('start-text');

  // ==========================================
  // ★ 画面シェイク機能
  // ==========================================
  let screenShake = {{ x: 0, y: 0, duration: 0, intensity: 0 }};
  function addShake(intensity, duration) {{ screenShake.intensity = intensity; screenShake.duration = duration; }}
  function updateShake() {{
      if (screenShake.duration > 0) {{
          screenShake.x = (Math.random() - 0.5) * screenShake.intensity;
          screenShake.y = (Math.random() - 0.5) * screenShake.intensity;
          screenShake.duration--;
      }} else {{ screenShake.x = 0; screenShake.y = 0; }}
  }}

  // ==========================================
  // ★ パーティクルシステム
  // ==========================================
  let particles = [];
  function spawnParticles(x, y, color, count = 8) {{
      for (let i = 0; i < count; i++) {{
          particles.push({{ x: x, y: y, vx: (Math.random() - 0.5) * 8, vy: (Math.random() - 0.5) * 8, life: 30 + Math.random() * 20, size: 4 + Math.random() * 4, color: color }});
      }}
  }}
  function updateAndDrawParticles() {{
      for (let i = 0; i < particles.length; i++) {{
          let p = particles[i];
          p.x += p.vx; p.y += p.vy; p.vy += 0.2; p.life--; p.size *= 0.95;
          // 描画はdraw関数内で行う
          if (p.life <= 0 || p.size < 0.5) {{ particles.splice(i, 1); i--; }}
      }}
  }}

  // ==========================================
  // BGM設定
  // ==========================================
  let audioCtx, isBgmPlaying = false, bgmTimeout = null, activeOscillators = [];
  const BASE_BPM = 130, BASE_BEAT_TIME = 60 / BASE_BPM;
  const melody = [5,5,6,5,3,-1,3,5, 5,5,6,5,3,-1,3,2, 5,5,6,5,8,8,7,6, 6,5,3,3,-1,5,-1,-1];
  const scaleToFreq = (num) => {{ if(num < 0) return null; const scale = [261.63,293.66,329.63,349.23,392.00,440.00,493.88,523.25]; return scale[num-1]; }};

  function playNoiseForBGM(time, duration, volume){{
      if (audioCtx.state === 'suspended') audioCtx.resume();
      const buffer = audioCtx.createBuffer(1, audioCtx.sampleRate * duration, audioCtx.sampleRate);
      const data = buffer.getChannelData(0); for(let i=0;i<data.length;i++) data[i] = (Math.random()*2-1);
      const noise = audioCtx.createBufferSource(); noise.buffer = buffer;
      const gain = audioCtx.createGain(); gain.gain.setValueAtTime(volume, time); gain.gain.exponentialRampToValueAtTime(0.01, time + duration);
      noise.connect(gain).connect(audioCtx.destination); noise.start(time); activeOscillators.push(noise);
  }}
  function playNoteForBGM(freq, time, duration){{
      if (audioCtx.state === 'suspended') audioCtx.resume();
      const osc = audioCtx.createOscillator(); osc.type = "square"; osc.frequency.value = freq;
      const gain = audioCtx.createGain(); gain.gain.setValueAtTime(0.15, time); gain.gain.exponentialRampToValueAtTime(0.01, time + duration);
      osc.connect(gain).connect(audioCtx.destination); osc.start(time); osc.stop(time + duration); activeOscillators.push(osc);
  }}
  function getCurrentBeatTime() {{ let multiplier = 1.0 + Math.min(score, 10000) / 10000 * 3.0; return BASE_BEAT_TIME / multiplier; }}
  function playBGMLoop(){{
      if (!isBgmPlaying) return; 
      const start = audioCtx.currentTime; const currentBeat = getCurrentBeatTime(); 
      melody.forEach((note,i)=>{{ const t = start + i * currentBeat; if(note > 0) playNoteForBGM(scaleToFreq(note), t, currentBeat); else playNoiseForBGM(t, 0.03, 0.1); }});
      bgmTimeout = setTimeout(playBGMLoop, melody.length * currentBeat * 1000);
  }}
  function startBGM() {{ if (isBgmPlaying) return; isBgmPlaying = true; if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)(); if (audioCtx.state === 'suspended') audioCtx.resume(); playBGMLoop(); }}
  function stopBGM() {{ isBgmPlaying = false; if (bgmTimeout) clearTimeout(bgmTimeout); activeOscillators.forEach(node => {{ try {{ node.stop(); }} catch(e) {{}} }}); activeOscillators = []; }}
  function playGameOverSound() {{
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)(); if (audioCtx.state === 'suspended') audioCtx.resume();
      const osc = audioCtx.createOscillator(); const gain = audioCtx.createGain(); osc.type = 'sawtooth'; osc.connect(gain); gain.connect(audioCtx.destination);
      const now = audioCtx.currentTime; osc.frequency.setValueAtTime(800, now); osc.frequency.exponentialRampToValueAtTime(50, now + 0.8); gain.gain.setValueAtTime(0.3, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.8); osc.start(now); osc.stop(now + 0.8);
  }}

  // ==========================================
  // 画像読み込み
  // ==========================================
  function loadResized(src, w, h) {{
      const wrapper = {{ img: null, ready: false, error: false }};
      const img = new Image(); img.crossOrigin = "Anonymous"; img.src = src;
      img.onload = () => {{
          const offCanvas = document.createElement('canvas'); offCanvas.width = w; offCanvas.height = h;
          const offCtx = offCanvas.getContext('2d'); offCtx.drawImage(img, 0, 0, w, h);
          wrapper.img = offCanvas; wrapper.ready = true;
      }};
      img.onerror = () => {{ wrapper.error = true; }};
      return wrapper;
  }}

  const P_W = 60, P_H = 60; 
  const playerAnim = {{ idle: [], run: [], jump: [], dead: null, squat: null }};
  for(let i=1; i<=3; i++) playerAnim.idle.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Taiki0${{i}}.png`, P_W, P_H));
  for(let i=1; i<=3; i++) playerAnim.run.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Run0${{i}}.png`, P_W, P_H));
  for(let i=1; i<=3; i++) playerAnim.jump.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Jump0${{i}}.png`, P_W, P_H));
  playerAnim.dead = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/Dead.png", P_W, P_H);
  playerAnim.squat = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/squat.png", P_W, P_H);

  const enemyAnim = [], enemy2Anim = [];
  for(let i=1; i<=2; i++) {{ enemyAnim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/EnemyAction0${{i}}.png`, 52, 52)); }}
  for(let i=1; i<=2; i++) {{ enemy2Anim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Enemy2Action0${{i}}.png`, 52, 52)); }}
  
  const itemImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png", 45, 45);
  const capsuleImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/capsule.png", 45, 45);
  const mutekiImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/muteki.png", 45, 45);
  const jyamaImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/jyama.png", 45, 45);
  
  const itemEffectAnim = [];
  for(let i=1; i<=3; i++) itemEffectAnim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/ItemAction0${{i}}.png`, 45, 45));

  const cloudImgWrappers = [];
  for(let i=1; i<=4; i++) cloudImgWrappers.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/cloud${{i}}.png`, 170, 120)); 

  // ★追加: 背景画像（山、建物）
  // ⚠️ご自身の画像URLに置き換えてください。とりあえずダミーURLを入れておきます。
  // サイズは適当に大きめに指定（画面幅より大きく）
  const mountainImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/mountains.png", 1200, 400);
  const buildingImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/buildings.png", 1000, 300);

  // ゲーム変数
  const GRAVITY = 0.6, FRICTION = 0.8, BASE_GROUND_Y = 360;  
  let score = 0, level = 1, gameSpeed = 1.0, hp = 3, gameOver = false, isTitle = true; 
  let frameCount = 0, nextEnemySpawn = 0, nextItemSpawn = 0;
  let facingRight = true, isInvincible = false, invincibleTimer = 0, terrainSegments = [];
  let superMode = false, superModeTimer = 0, slowMode = false, slowModeTimer = 0;
  let floatingTexts = [], autoRestartTimer = null;
  
  let cameraX = 0;
  let lastGeneratedX = 0;
  
  let platforms = [];
  let checkpoints = [];
  let nextCheckpointDist = 800 * 10; 

  const player = {{ 
      x: 200, y: 0, width: 60, height: 60, 
      speed: 7, 
      dx: 0, dy: 0, 
      jumping: false, jumpCount: 0, maxJump: 2,
      state: 'idle', animIndex: 0, animTimer: 0, 
      animSpeedIdle: 15, animSpeedRun: 8, idlePingPong: 1, combo: 0 
  }};
  
  let enemies = [], items = [], clouds = [];
  const keys = {{ right: false, left: false, up: false, down: false }}; 

  const API_URL = "{GAS_API_URL}";
  let globalRankings = [];

  async function fetchRankings() {{
    try {{ const response = await fetch(API_URL); return await response.json(); }} catch (e) {{ console.error(e); return []; }}
  }}
  async function sendScore(name, score) {{
    try {{ await fetch(API_URL, {{ method: 'POST', body: JSON.stringify({{ name: name, score: score }}) }}); }} catch (e) {{ console.error(e); }}
  }}
  fetchRankings().then(data => {{ globalRankings = data; }});

  function checkRankIn(currentScore) {{
    if (globalRankings.length < 10) return true;
    return currentScore > globalRankings[globalRankings.length - 1].score;
  }}
  function startAutoRestartCountdown() {{
      let count = 5; autoRestartMsg.style.display = 'block'; autoRestartMsg.innerText = `Restarting in ${{count}}...`;
      if (autoRestartTimer) clearInterval(autoRestartTimer);
      autoRestartTimer = setInterval(() => {{
          count--; if (count > 0) autoRestartMsg.innerText = `Restarting in ${{count}}...`;
          else {{ clearInterval(autoRestartTimer); resetGame(); }}
      }}, 1000);
  }}
  async function submitScore() {{
    const name = nameInput.value.trim() || "NO NAME";
    nameInput.disabled = true; submitBtn.disabled = true; loadingMsg.style.display = 'block';
    await sendScore(name, score); globalRankings = await fetchRankings();
    loadingMsg.style.display = 'none'; nameInput.disabled = false; submitBtn.disabled = false;
    inputSection.style.display = 'none'; showRankingTable(globalRankings);
    if (isMobile) startAutoRestartCountdown();
  }}
  function showRankingTable(rankings) {{
    if (!rankings) rankings = globalRankings; rankingBody.innerHTML = "";
    for (let i = 0; i < 10; i++) {{
        let r = rankings[i]; let row = document.createElement('tr');
        if (r) row.innerHTML = `<td class="rank-col">${{i + 1}}</td><td style="${{r.score === score && r.name === nameInput.value ? "color: yellow; font-weight:bold;" : ""}}">${{r.name}}</td><td class="score-col">${{r.score}}</td>`;
        else row.innerHTML = `<td class="rank-col">${{i + 1}}</td><td>---</td><td class="score-col">0</td>`;
        rankingBody.appendChild(row);
    }}
  }}
  function handleGameOver() {{
    gameOver = true; player.state = 'dead'; stopBGM(); playGameOverSound(); addShake(15, 20); 
    overlay.style.display = 'block'; finalScoreDisplay.innerText = "Final Score: " + score;
    nameInput.value = ""; rankingBody.innerHTML = ""; rankLoading.style.display = "block";
    fetchRankings().then(data => {{
        globalRankings = data; rankLoading.style.display = "none"; showRankingTable(globalRankings);
        if (score > 0 && checkRankIn(score)) {{ inputSection.style.display = 'block'; nameInput.focus(); }} 
        else {{ inputSection.style.display = 'none'; if (isMobile) startAutoRestartCountdown(); }}
    }});
  }}
  function playSound(type) {{
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)(); if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator(); const gain = audioCtx.createGain(); osc.connect(gain); gain.connect(audioCtx.destination); const now = audioCtx.currentTime;
    if (type === 'jump') {{ osc.type = 'square'; osc.frequency.setValueAtTime(150, now); osc.frequency.linearRampToValueAtTime(300, now + 0.1); gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1); osc.start(now); osc.stop(now + 0.1); }} 
    else if (type === 'coin') {{ osc.type = 'sine'; osc.frequency.setValueAtTime(1200, now); osc.frequency.setValueAtTime(1600, now + 0.05); gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2); osc.start(now); osc.stop(now + 0.2); }} 
    else if (type === 'hit') {{ osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, now); osc.frequency.linearRampToValueAtTime(50, now + 0.3); gain.gain.setValueAtTime(0.2, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3); osc.start(now); osc.stop(now + 0.3); }} 
    else if (type === 'heal') {{ osc.type = 'sine'; osc.frequency.setValueAtTime(400, now); osc.frequency.linearRampToValueAtTime(800, now + 0.2); gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.3); osc.start(now); osc.stop(now + 0.3); }} 
    else if (type === 'powerup') {{ osc.type = 'square'; osc.frequency.setValueAtTime(440, now); osc.frequency.setValueAtTime(880, now + 0.1); gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.5); osc.start(now); osc.stop(now + 0.5); }} 
    else if (type === 'bad') {{ osc.type = 'sawtooth'; osc.frequency.setValueAtTime(300, now); osc.frequency.linearRampToValueAtTime(150, now + 0.3); gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.3); osc.start(now); osc.stop(now + 0.3); }}
    else if (type === 'gate') {{ osc.type = 'sine'; osc.frequency.setValueAtTime(800, now); osc.frequency.linearRampToValueAtTime(1200, now + 0.3); gain.gain.setValueAtTime(0.2, now); gain.gain.linearRampToValueAtTime(0, now + 0.4); osc.start(now); osc.stop(now + 0.4); }}
  }}
  function doJump() {{
      if (!gameOver && !isTitle) {{
          if (!player.jumping || player.jumpCount < player.maxJump) {{
              player.jumping = true; player.dy = -12; player.jumpCount++; playSound('jump'); startBGM();
          }}
      }}
  }}

  const btnLeft = document.getElementById('btn-left');
  const btnRight = document.getElementById('btn-right');
  const btnDown = document.getElementById('btn-down');
  const btnJump = document.getElementById('btn-jump');
  document.addEventListener('touchstart', function(e) {{ if (e.target.classList.contains('touch-btn')) e.preventDefault(); }}, {{ passive: false }});
  if(btnLeft) {{ btnLeft.addEventListener('touchstart', (e) => {{ keys.left = true; facingRight = false; startBGM(); }}); btnLeft.addEventListener('touchend', (e) => {{ keys.left = false; }}); }}
  if(btnRight) {{ btnRight.addEventListener('touchstart', (e) => {{ keys.right = true; facingRight = true; startBGM(); }}); btnRight.addEventListener('touchend', (e) => {{ keys.right = false; }}); }}
  if(btnDown) {{ btnDown.addEventListener('touchstart', (e) => {{ keys.down = true; startBGM(); }}); btnDown.addEventListener('touchend', (e) => {{ keys.down = false; }}); }}
  if(btnJump) {{ btnJump.addEventListener('touchstart', (e) => {{ doJump(); }}); }}
  document.addEventListener('keydown', (e) => {{
    if (document.activeElement === nameInput) {{ if (e.key === 'Enter' && !submitBtn.disabled) submitScore(); return; }}
    if (player.state === 'dead' && e.code !== 'KeyR') return;
    if (e.code === 'KeyF') {{ if (!document.fullscreenElement) document.documentElement.requestFullscreen(); else if (document.exitFullscreen) document.exitFullscreen(); }}
    if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyR', 'KeyF'].includes(e.code)) {{ e.preventDefault(); }}
    if (e.code === 'KeyD') {{ keys.right = true; facingRight = true; startBGM(); }} if (e.code === 'KeyA') {{ keys.left = true; facingRight = false; startBGM(); }} if (e.code === 'KeyS') {{ keys.down = true; startBGM(); }} if (e.code === 'KeyW') {{ doJump(); }}
    if (e.code === 'KeyR' && gameOver) resetGame();
  }});
  document.addEventListener('keyup', (e) => {{ if (e.code === 'KeyD') keys.right = false; if (e.code === 'KeyA') keys.left = false; if (e.code === 'KeyS') keys.down = false; }});

  // ★ 横スクロール用の地形生成ロジック（無限生成）
  function updateTerrain() {{
      const deleteThreshold = cameraX - 200;
      for (let i = 0; i < terrainSegments.length; i++) {{
          if (terrainSegments[i].x + terrainSegments[i].width < deleteThreshold) {{ terrainSegments.splice(i, 1); i--; }}
      }}
      for (let i = 0; i < platforms.length; i++) {{
          if (platforms[i].x + platforms[i].width < deleteThreshold) {{ platforms.splice(i, 1); i--; }}
      }}
      for (let i = 0; i < checkpoints.length; i++) {{
          if (checkpoints[i].x + 100 < deleteThreshold) {{ checkpoints.splice(i, 1); i--; }}
      }}
      
      const generateThreshold = cameraX + canvas.width + 200;
      while (lastGeneratedX < generateThreshold) {{
          generateNextSegment();
      }}
      
      // ★ 修正3: チェックポイント生成 (10画面ごと)
      if (lastGeneratedX > nextCheckpointDist) {{
          checkpoints.push({{ x: nextCheckpointDist, passed: false }});
          nextCheckpointDist += 800 * 10;
      }}
  }}

  function generateNextSegment() {{
      if (terrainSegments.length === 0) {{
          terrainSegments.push({{ x: 0, width: 800, topY: BASE_GROUND_Y, level: 0 }});
          lastGeneratedX = 800;
          return;
      }}

      let prevSeg = terrainSegments[terrainSegments.length - 1];
      let gapWidth = 0;
      if (Math.random() < 0.25 && prevSeg.width > 100) gapWidth = Math.random() * 100 + 80; 

      let newX = lastGeneratedX + gapWidth;
      let width = Math.random() * 200 + 150; 
      
      const SEG_HEIGHTS = [BASE_GROUND_Y, BASE_GROUND_Y - 50, BASE_GROUND_Y - 100];
      let prevLevel = prevSeg.level !== undefined ? prevSeg.level : 0;
      let delta = Math.floor(Math.random() * 3) - 1; 
      let newLevel = Math.min(2, Math.max(0, prevLevel + delta));
      let topY = SEG_HEIGHTS[newLevel];

      terrainSegments.push({{ x: newX, width: width, topY: topY, level: newLevel }});
      lastGeneratedX = newX + width;

      // ★ 修正2: 空中コンクリート生成 (30%の確率)
      if (Math.random() < 0.3) {{
          let pW = player.width * (3 + Math.random() * 2); // 3~5倍幅
          let pX = newX + Math.random() * (width - pW); 
          let pY = topY - 100 - Math.random() * 80; 
          if (pY < 100) pY = 100;
          platforms.push({{ x: pX, y: pY, width: pW, height: 20 }});
          
          // プラットフォーム上にも敵やアイテム
          if (Math.random() < 0.5) spawnEnemyOnTerrain(pX, pW, pY);
      }}

      if (gapWidth === 0 && width > 100) {{
           // ★修正1: 出現頻度2倍 (0.5->1.0, 0.4->0.8)
           if (Math.random() < 1.0) spawnEnemyOnTerrain(newX, width, topY);
           if (Math.random() < 0.8) spawnItemOnTerrain(newX, width, topY);
      }}
  }}
  
  function spawnEnemyOnTerrain(tx, tw, ty) {{
      let type = Math.random() < 0.5 ? 'ground' : 'flying';
      let speedBase = 2 + level * 0.05; 
      let ex = tx + Math.random() * (tw - 60) + 30; 
      let ey = ty - 52; 

      if (type === 'flying') ey = ty - 100 - Math.random() * 100; 
      if (score >= 2000 && Math.random() < 0.3) {{ type = 'hard'; speedBase += 2; }}
      
      enemies.push({{ x: ex, y: ey, width: 52, height: 52, dx: -speedBase, dy: 0, type: type, angle: 0, animIndex: 0, animTimer: 0 }});
  }}

  function spawnItemOnTerrain(tx, tw, ty) {{
      const r = Math.random();
      let type = 'coin';
      if (r < 0.005) type = 'star'; else if (r < 0.035) type = 'trap'; else if (r < 0.045) type = 'heal'; else type = 'coin';

      let ix = tx + Math.random() * (tw - 50) + 25;
      let iy = ty - 45 - Math.random() * 100; 
      
      items.push({{ x: ix, y: iy, width: 45, height: 45, dx: 0, isCollected: false, animIndex: 0, animTimer: 0, type: type }}); 
  }}
  
  // ★ 修正: 地形とプラットフォームの両方で地面高さをチェック
  function getGroundYUnderPlayer() {{
    let groundY = null;
    let centerX = player.x + player.width / 2;
    
    // 地形
    for (let seg of terrainSegments) {{ 
        if (centerX > seg.x && centerX < seg.x + seg.width) {{ 
            if (groundY === null || seg.topY < groundY) groundY = seg.topY; 
        }} 
    }}
    // プラットフォーム (プレイヤーが上にいる場合のみ有効)
    for (let p of platforms) {{
        if (centerX > p.x && centerX < p.x + p.width) {{
             // 足元がプラットフォームより上にある場合のみ着地対象
             if (player.y + player.height <= p.y + 20) {{
                 if (groundY === null || p.y < groundY) groundY = p.y;
             }}
        }}
    }}
    return groundY;
  }}
  
  function getGroundYAtX(x) {{
    let groundY = null;
    for (let seg of terrainSegments) {{ if (x >= seg.x && x <= seg.x + seg.width) {{ if (groundY === null || seg.topY < groundY) groundY = seg.topY; }} }}
    // プラットフォームは壁判定には含めない（すり抜け可能にするため）
    return groundY;
  }}

  function initClouds() {{
    clouds = [];
    for(let i=0; i<8; i++) {{ clouds.push({{ x: Math.random() * 1200, y: Math.random() * 200, speed: Math.random() * 0.3 + 0.1, imgIndex: Math.floor(Math.random() * 4) }}); }}
  }}

  // ★ 雲の更新 (修正2: パララックス考慮の判定)
  function updateClouds() {{
    for(let c of clouds) {{
        c.x -= c.speed;
        
        // 描画位置(parallaxX) = c.x + cameraX * 0.8
        // 画面左端(cameraX) より左(-200)に行ったら消える判定
        // c.x + cameraX * 0.8 < cameraX - 200
        // c.x < 0.2 * cameraX - 200
        
        if(c.x < 0.2 * cameraX - 200) {{ 
            // 右端から再出現させる
            // c.x = 0.2 * cameraX + 800 + random
            c.x = 0.2 * cameraX + canvas.width + 200 + Math.random() * 200; 
            c.y = Math.random() * 150; // Y座標もランダムに
            c.imgIndex = Math.floor(Math.random() * 4);
        }}
    }}
  }}

  function updateLevel() {{ const newLevel = Math.floor(score / 500) + 1; if (newLevel > level) {{ level = newLevel; gameSpeed = 1.0 + (level * 0.05); levelEl.innerText = level; if(hp < 3) {{ hp++; updateHearts(); }} }} }}

  function updateHearts() {{ let h = ""; for(let i=0; i<hp; i++) h += "❤️"; heartsEl.innerText = h; }}

  function resetGame() {{
    if (autoRestartTimer) clearInterval(autoRestartTimer);
    autoRestartMsg.style.display = 'none';

    // ★ 座標リセット
    player.x = 200; player.y = 0; player.dx = 0; player.dy = 0;
    cameraX = 0; lastGeneratedX = 0;
    
    player.state = 'idle'; player.animIndex = 0; player.animTimer = 0; player.idlePingPong = 1;
    player.combo = 0; player.jumpCount = 0;
    score = 0; level = 1; gameSpeed = 1.0; hp = 3;
    enemies = []; items = []; floatingTexts = []; particles = []; terrainSegments = []; 
    platforms = []; checkpoints = []; nextCheckpointDist = 800 * 10; // リセット
    
    gameOver = false; frameCount = 0;
    isInvincible = false; nextEnemySpawn = 0; nextItemSpawn = 0;
    scoreEl.innerText = score; levelEl.innerText = level;
    superMode = false; superModeTimer = 0; slowMode = false; slowModeTimer = 0; statusMsgEl.innerText = "";

    isTitle = true; titleScreen.style.display = 'flex';
    titleImg.style.animation = 'none'; void titleImg.offsetWidth; titleImg.style.animation = 'slideUpFade 2s forwards';
    startText.style.opacity = '0'; startText.style.animation = 'none';
    setTimeout(() => {{ startText.style.animation = 'blinkFade 0.5s forwards'; setTimeout(() => {{ titleScreen.style.display = 'none'; isTitle = false; }}, 1000); }}, 2000);

    updateHearts(); initClouds(); updateTerrain(); // 初回の地形生成
    const startGround = getGroundYUnderPlayer(); 
    const gY = startGround !== null ? startGround : BASE_GROUND_Y; 
    player.y = gY - player.height;
    overlay.style.display = 'none';
  }}

  function updatePlayerAnimation() {{
    const prevState = player.state;
    if (hp <= 0) player.state = 'dead';
    else if (player.jumping) player.state = 'jump';
    else if (keys.down) player.state = 'squat';
    else if (keys.right || keys.left) player.state = 'run';
    else player.state = 'idle';

    if (player.state !== prevState) {{ player.animTimer = 0; player.animIndex = 0; player.idlePingPong = 1; }}
    player.animTimer++;
    switch (player.state) {{
        case 'idle': if (player.animTimer > player.animSpeedIdle) {{ player.animIndex += player.idlePingPong; if (player.animIndex >= 2) player.idlePingPong = -1; if (player.animIndex <= 0) player.idlePingPong = 1; player.animTimer = 0; }} break;
        case 'run': if (player.animTimer > player.animSpeedRun) {{ player.animIndex = (player.animIndex + 1) % 3; player.animTimer = 0; }} break;
        case 'jump': if (player.dy < -5) player.animIndex = 0; else if (player.dy < 0) player.animIndex = 1; else if (player.dy < 5) player.animIndex = 2; else player.animIndex = 1; break;
        case 'squat': player.animIndex = 0; break;
        case 'dead': player.animIndex = 0; break;
    }}
  }}

  function update() {{
    if (gameOver && player.state !== 'dead') return; if (player.state === 'dead') return;
    if (isTitle) {{ updateClouds(); return; }}

    updateShake(); frameCount++; updateClouds();
    if (isInvincible) {{ invincibleTimer--; if (invincibleTimer <= 0) isInvincible = false; }}
    
    let statusText = "";
    if (superMode) {{ superModeTimer--; statusText += "🌟SUPER MODE! "; if (superModeTimer <= 0) superMode = false; }}
    if (slowMode) {{ slowModeTimer--; statusText += "🐢SLOW... "; if (slowModeTimer <= 0) slowMode = false; }}
    statusMsgEl.innerText = statusText;
    if (superMode) statusMsgEl.style.color = "gold"; else if (slowMode) statusMsgEl.style.color = "violet"; else statusMsgEl.innerText = "";

    let currentSpeed = player.speed;
    if (slowMode) currentSpeed *= 0.5;

    if (player.state !== 'dead') {{
        // しゃがみ中は移動不可
        if (player.state !== 'squat') {{
            if (keys.right) player.dx = currentSpeed;
            else if (keys.left) player.dx = -currentSpeed;
            else player.dx *= FRICTION;
        }} else {{
            player.dx *= FRICTION;
        }}

        let nextX = player.x + player.dx;
        let checkX = player.dx > 0 ? nextX + player.width : nextX;
        let nextGroundY = getGroundYAtX(checkX); 
        
        // 段差判定
        if (nextGroundY !== null) {{
            if (player.y + player.height > nextGroundY + 5) {{ player.dx = 0; }}
        }}
        
        // 左端制限 (カメラより左には行けない)
        if (nextX < cameraX) {{
            nextX = cameraX;
            player.dx = 0;
        }}
    }}

    player.x += player.dx; player.y += player.dy; player.dy += GRAVITY;
    
    // ★ カメラ更新: プレイヤーが画面中央(400px)を超えたらカメラを追従させる
    let targetCameraX = player.x - 300; // 画面左から300pxの位置にプレイヤーを置くイメージ
    if (targetCameraX < 0) targetCameraX = 0;
    if (targetCameraX > cameraX) {{
        cameraX = targetCameraX; // 前進のみ（戻れない）
    }}
    
    // ★ 地形無限生成 & 削除
    updateTerrain();

    // 落下判定
    const groundY = getGroundYUnderPlayer();
    if (groundY !== null) {{ 
        if (player.y + player.height >= groundY && player.dy >= 0) {{ 
            player.y = groundY - player.height; 
            player.dy = 0; 
            player.jumping = false; 
            player.combo = 0; 
            player.jumpCount = 0; 
        }} 
    }} else {{ 
        if (player.y > canvas.height) {{ 
            if (isNaN(player.y)) player.y = 0; 
            if (!gameOver) {{ hp = 0; updateHearts(); playSound('hit'); handleGameOver(); }} 
        }} 
    }}
    
    updatePlayerAnimation();
    if (gameOver) return;

    // パーティクル更新
    updateAndDrawParticles(); // 計算のみ

    // フローティングテキスト更新
    for (let i = 0; i < floatingTexts.length; i++) {{
        let ft = floatingTexts[i]; ft.y += ft.dy; ft.life--; if (ft.life <= 0) {{ floatingTexts.splice(i, 1); i--; }}
    }}

    let playerHitH = player.height; let playerHitY = player.y;
    if (player.state === 'squat') {{ playerHitH = player.height / 2; playerHitY = player.y + player.height / 2; }}

    // ★ アイテム更新 (削除判定はカメラ基準)
    for (let i = 0; i < items.length; i++) {{ 
        let item = items[i]; 
        
        // 画面左外に出たら消す
        if (item.x + item.width < cameraX - 100) {{ items.splice(i, 1); i--; continue; }}

        if (item.isCollected) {{
            if (item.type === 'coin') {{ item.animTimer++; if (item.animTimer > 5) {{ item.animIndex++; item.animTimer = 0; }} if (item.animIndex >= 3) {{ items.splice(i, 1); i--; }} }} 
            else {{ item.animTimer++; if (item.animTimer > 30) {{ items.splice(i, 1); i--; }} }}
        }} else {{
            // アイテムは動かない(dx=0)
            if (player.x < item.x + item.width && player.x + player.width > item.x && playerHitY < item.y + item.height && playerHitY + playerHitH > item.y) {{
                item.isCollected = true; item.animIndex = 0; item.animTimer = 0;
                if (item.type === 'coin') {{ score += 50; playSound('coin'); spawnParticles(item.x, item.y, 'gold', 5); }} 
                else if (item.type === 'heal') {{ hp = 3; updateHearts(); playSound('heal'); spawnParticles(item.x, item.y, 'pink', 8); }} 
                else if (item.type === 'star') {{ superMode = true; superModeTimer = 900; isInvincible = true; invincibleTimer = 900; slowMode = false; slowModeTimer = 0; playSound('powerup'); spawnParticles(item.x, item.y, 'yellow', 10); }} 
                else if (item.type === 'trap') {{ if (!superMode) {{ slowMode = true; slowModeTimer = 600; playSound('bad'); spawnParticles(item.x, item.y, 'purple', 8); }} }}
                scoreEl.innerText = score; updateLevel(); 
            }}
        }}
    }}

    // ★ 敵更新
    let stompedThisFrame = false; 
    for (let i = 0; i < enemies.length; i++) {{ 
        let e = enemies[i]; 
        
        // 画面左外に出たら消す
        if (e.x + e.width < cameraX - 100) {{ enemies.splice(i, 1); i--; continue; }}

        // 敵の移動 (対地速度で動く)
        e.x += e.dx;
        
        e.animTimer++; if (e.animTimer > 10) {{ e.animIndex = (e.animIndex + 1) % 2; e.animTimer = 0; }}
        if (e.type === 'flying') {{ e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }} 

        if (player.x < e.x + e.width && player.x + player.width > e.x && playerHitY < e.y + e.height && playerHitY + playerHitH > e.y) {{ 
            const isStomp = (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) || stompedThisFrame || superMode;
            if (isStomp) {{ 
                enemies.splice(i, 1); i--; 
                if (!superMode) {{ player.dy = -10; stompedThisFrame = true; }}
                player.combo++; let multiplier = Math.pow(2, player.combo - 1); let bonusPoints = 100 * multiplier;
                score += bonusPoints; scoreEl.innerText = score; playSound('coin'); updateLevel(); 
                if (multiplier > 1) {{ floatingTexts.push({{ x: player.x, y: player.y - 20, text: "BONUS x" + multiplier, life: 60, dy: -1.5 }}); }}
                spawnParticles(e.x, e.y, 'red', 8);
            }} else {{ 
                if (!isInvincible) {{ 
                    hp--; if (hp < 0) hp = 0; updateHearts(); playSound('hit'); addShake(15, 20);
                    if (hp <= 0) handleGameOver(); else {{ isInvincible = true; invincibleTimer = 60; enemies.splice(i, 1); i--; }} 
                }} 
            }} 
        }} 
    }}
  }}

  // ★追加: パララックス背景描画関数
  function drawParallaxLayer(imgWrapper, scrollFactor, y) {{
      if (!imgWrapper || !imgWrapper.ready) return;
      const img = imgWrapper.img;
      const w = img.width;
      const h = img.height;
      
      // カメラ位置に応じたオフセット（ループ）
      let x = -(cameraX * scrollFactor) % w;
      
      if (x > 0) x -= w;
      while (x < canvas.width) {{
          ctx.drawImage(img, x, y);
          x += w;
      }}
  }}

  function drawObj(wrapper, x, y, w, h, fallbackColor) {{
    if (wrapper && wrapper.ready && wrapper.img) ctx.drawImage(wrapper.img, x, y, w, h);
    else {{ ctx.fillStyle = fallbackColor; ctx.fillRect(x, y, w, h); }}
  }}

  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    let skyColor;
    if (score < 1000) skyColor = '#87CEEB'; else if (score < 3000) skyColor = '#FF7F50'; else if (score < 5000) skyColor = '#191970'; else skyColor = '#4B0082'; 
    ctx.fillStyle = skyColor; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // ★追加: パララックス背景描画 (シェイク影響なし)
    // シェイク前のコンテキスト保存は不要(背景なので揺らさない方が酔いにくいが、今回は全体揺らすならsave/restoreの外でやるべき)
    // ここでは全体揺らす方針で、translateの後に描画する。
    
    ctx.save();
    ctx.translate(screenShake.x, screenShake.y);

    // 山 (遠景)
    // y位置は画面下端基準で調整 (canvas.height - img.height) だが、少し沈めるなど調整
    // ここでは loadResized で 400px 高さにしてるので 0 から描画でOKかも
    drawParallaxLayer(mountainImgWrapper, 0.1, canvas.height - 300); // 少し上に

    // 雲
    // 雲は個別に動くオブジェクトとして実装されているのでそのまま
    // ただし drawParallaxLayer ではなく個別の updateClouds で位置管理されている
    // updateClouds で parallaxX を計算して描画しているロジックを維持
    for(let c of clouds) {{
        let wrapper = cloudImgWrappers[c.imgIndex];
        let parallaxX = c.x - cameraX * 0.2; // カメラの影響を弱める（パララックス）
        // ループ処理はupdateCloudsでやっているが、描画位置だけ補正
        // updateCloudsのロジック: c.x は絶対座標。
        // 描画位置 = c.x - cameraX (通常)
        // パララックス = c.x - cameraX * factor
        // ここでは既存ロジックを生かすため、絶対座標からカメラ分を引く
        // ただし雲は updateClouds でカメラ位置に応じて位置リセットされているので
        // 単純に drawImage(img, c.x - cameraX, c.y) でよいが、
        // 既存コードは `ctx.translate(-cameraX)` している前提で `ctx.drawImage(..., parallaxX, ...)` している
        // ここでは `drawParallaxLayer` を使わず、既存の雲描画ロジックを維持・調整する
        
        // 手動でパララックス計算して描画
        let drawX = c.x - cameraX * 0.2; 
        // 画面内ループさせるためにモジュロ的な処理が必要だが、updateCloudsで管理されているのでそのまま
        if (wrapper && wrapper.ready && wrapper.img) {{ ctx.drawImage(wrapper.img, drawX, c.y); }} 
        else {{ ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'; ctx.beginPath(); ctx.arc(drawX, c.y, 30, 0, Math.PI*2); ctx.fill(); }}
    }}

    // 建物 (中景)
    drawParallaxLayer(buildingImgWrapper, 0.4, canvas.height - 250); // 下揃え

    // メインコンテンツ（カメラ追従）
    ctx.translate(-cameraX, 0); // カメラ分ずらす

    for (let seg of terrainSegments) {{ ctx.fillStyle = '#654321'; ctx.fillRect(seg.x, seg.topY, seg.width, canvas.height - seg.topY); ctx.fillStyle = '#228B22'; ctx.fillRect(seg.x, seg.topY, seg.width, 10); }}
    
    // ★ 追加: プラットフォーム描画
    ctx.fillStyle = '#999';
    ctx.strokeStyle = '#555';
    for (let p of platforms) {{
        ctx.fillRect(p.x, p.y, p.width, p.height);
        ctx.strokeRect(p.x, p.y, p.width, p.height);
    }}

    // ★ 追加: ゲート描画
    ctx.strokeStyle = 'yellow';
    ctx.lineWidth = 5;
    for (let cp of checkpoints) {{
        ctx.beginPath();
        ctx.moveTo(cp.x, BASE_GROUND_Y);
        ctx.lineTo(cp.x, BASE_GROUND_Y - 150);
        ctx.arc(cp.x + 40, BASE_GROUND_Y - 150, 40, Math.PI, 0);
        ctx.lineTo(cp.x + 80, BASE_GROUND_Y);
        ctx.stroke();
        if (!cp.passed) {{
             ctx.fillStyle = 'rgba(0, 255, 255, 0.3)';
             ctx.fill();
        }}
    }}

    for (let item of items) {{
        if (item.isCollected) {{
            if (item.type === 'coin') {{ let effectWrapper = itemEffectAnim[item.animIndex]; if(effectWrapper) drawObj(effectWrapper, item.x, item.y, item.width, item.height, 'yellow'); }}
            else {{
                ctx.save(); if (Math.floor(Date.now() / 50) % 2 === 0) ctx.globalAlpha = 0.2; else ctx.globalAlpha = 0.8;
                if (item.type === 'heal') drawObj(capsuleImgWrapper, item.x, item.y, item.width, item.height, 'pink');
                else if (item.type === 'star') drawObj(mutekiImgWrapper, item.x, item.y, item.width, item.height, 'yellow');
                else if (item.type === 'trap') drawObj(jyamaImgWrapper, item.x, item.y, item.width, item.height, 'purple');
                ctx.restore();
            }}
        }} else {{
            if (item.type === 'coin') drawObj(itemImgWrapper, item.x, item.y, item.width, item.height, 'gold');
            else if (item.type === 'heal') drawObj(capsuleImgWrapper, item.x, item.y, item.width, item.height, 'pink');
            else if (item.type === 'star') drawObj(mutekiImgWrapper, item.x, item.y, item.width, item.height, 'yellow');
            else if (item.type === 'trap') drawObj(jyamaImgWrapper, item.x, item.y, item.width, item.height, 'purple');
        }}
    }}

    for (let e of enemies) {{ 
        let animWrapper = null;
        if (e.type === 'hard') {{ animWrapper = enemy2Anim[e.animIndex] || enemy2Anim[0]; drawObj(animWrapper, e.x, e.y, e.width, e.height, 'purple'); }} 
        else {{ animWrapper = enemyAnim[e.animIndex] || enemyAnim[0]; drawObj(animWrapper, e.x, e.y, e.width, e.height, 'red'); }}
    }}

    ctx.save();
    if (superMode) {{ if (Math.floor(Date.now() / 50) % 2 === 0) {{ ctx.globalAlpha = 0.8; ctx.filter = 'brightness(1.5) drop-shadow(0 0 5px gold)'; }} }} 
    else if (slowMode) {{ ctx.filter = 'hue-rotate(270deg)'; }} 
    else if (isInvincible) {{ if (Math.floor(Date.now() / 100) % 2 === 0) ctx.globalAlpha = 0.5; }}
    
    let currentWrapper = null;
    if (player.state === 'dead') currentWrapper = playerAnim.dead;
    else if (player.state === 'squat') currentWrapper = playerAnim.squat; 
    else if (playerAnim[player.state] && playerAnim[player.state][player.animIndex]) currentWrapper = playerAnim[player.state][player.animIndex];

    if (!isNaN(player.x) && !isNaN(player.y)) {{
        if (!facingRight) {{ ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); drawObj(currentWrapper, 0, 0, player.width, player.height, 'blue'); }} 
        else {{ drawObj(currentWrapper, player.x, player.y, player.width, player.height, 'blue'); }}
    }}
    ctx.restore();

    for(let p of particles) {{
        ctx.fillStyle = p.color; ctx.globalAlpha = Math.min(p.life / 20, 1.0); ctx.fillRect(p.x, p.y, p.size, p.size); ctx.globalAlpha = 1.0;
    }}

    ctx.fillStyle = "yellow"; ctx.font = "bold 20px Courier New"; ctx.strokeStyle = "black"; ctx.lineWidth = 3;
    for (let ft of floatingTexts) {{ ctx.strokeText(ft.text, ft.x, ft.y); ctx.fillText(ft.text, ft.x, ft.y); }}
    ctx.restore();
  }}

  function loop() {{ update(); draw(); requestAnimationFrame(loop); }}

  resetGame(); loop(); 
</script>
</body>
</html>
"""

components.html(game_html, height=550, scrolling=False)
