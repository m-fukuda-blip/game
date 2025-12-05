import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Game with Ranking & Animation", layout="wide")

# Streamlitの余計なUIを消して画面を固定するCSS
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        body {
            overflow: hidden !important;
            overscroll-behavior: none;
        }
    </style>
""", unsafe_allow_html=True)

# タイトル画像を表示
st.image("https://raw.githubusercontent.com/m-fukuda-blip/game/main/gametitlefix.png", use_column_width=True)

st.caption("機能：❤️ライフ / 🆙レベル / ☁️背景変化 / 🔊音 / 🏆ランク / 🏃‍♂️アニメ / 🎵BGM / ✨アイテム / 🧗‍♂️段差 / 💥コンボ / 🫨シェイク / 📏サイズ / 🦘2段ジャンプ / ✨撃破演出 / ⬇️しゃがみ / ⏩横スクロール / 🧱空中足場 / ⛩️ゲート / 🗻パララックス / 🕹️スティック操作 / 📱画面最適化 / 🔥ハードモード / 👑王冠ボーナス")
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
  html, body {{
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
  }}

  body {{ 
    overflow: hidden; 
    background-color: #222; 
    color: white; 
    font-family: 'Courier New', sans-serif; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    position: fixed; 
    top: 0; left: 0; right: 0; bottom: 0;
    overscroll-behavior: none;
    user-select: none;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
    touch-action: none;
  }}
  
  /* Canvas設定 */
  canvas {{ 
      background-color: #87CEEB; 
      border: 4px solid #fff; 
      box-shadow: 0 0 20px rgba(0,0,0,0.5);
      /* デフォルトではサイズ指定なし（JS制御） */
  }}
  
  /* スマホ横持ち時のCanvas最適化 */
  @media (max-height: 500px) and (orientation: landscape) {{
      canvas {{
          height: 100vh;       /* 画面の高さいっぱいに */
          width: auto;         /* アスペクト比維持 */
          max-width: 100vw;    /* 画面幅を超えない */
          object-fit: contain; /* 全体が収まるように */
          border: none;        /* 枠線を消してスッキリさせる */
      }}
  }}

  /* --- UIレイヤー --- */
  #ui-layer {{ 
      position: absolute; 
      top: 20px; left: 20px; 
      font-size: 24px; font-weight: bold; 
      color: black; 
      pointer-events: none; 
      text-shadow: 1px 1px 0 #fff; 
      z-index: 5; 
  }}

  /* スマホ横持ち時のUI配置調整 */
  @media (max-height: 500px) and (orientation: landscape) {{
      #ui-layer {{
          top: 220px; 
          left: 20px; 
          transform: scale(0.7); 
          transform-origin: top left;
          width: 100%;
      }}
  }}

  #hearts {{ color: red; font-size: 30px; }}
  #status-msg {{ font-size: 20px; margin-top: 5px; }}

  /* --- タイトル画面 --- */
  #title-screen {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    background: rgba(0,0,0,0.4); z-index: 10;
    pointer-events: none;
  }}
  
  .title-img {{ max-width: 22%; height: auto; margin-bottom: 20px; opacity: 0; }}
  @media (max-width: 800px) {{ .title-img {{ max-width: 60%; }} }}
  .start-text {{ font-size: 40px; color: white; text-shadow: 2px 2px #000; font-weight: bold; opacity: 0; }}
  
  @keyframes slideUpFade {{ 0% {{ opacity: 0; transform: translateY(100px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
  @keyframes blinkFade {{ 0% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
  @keyframes blinkRed {{ 0% {{ color: red; }} 50% {{ color: white; }} 100% {{ color: red; }} }}

  /* --- ゲームオーバー・ランキング画面 --- */
  #overlay {{ 
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
    background: rgba(0, 0, 0, 0.85); border: 4px solid white; border-radius: 10px;
    padding: 30px; text-align: center; color: white; display: none; width: 400px; 
    max-width: 90%; 
    z-index: 200; 
  }}

  @media (max-height: 500px) {{
      #overlay {{
          padding: 10px;
          transform: translate(-50%, -50%) scale(0.7); 
          width: 500px; 
      }}
      #final-score-display {{ margin-bottom: 5px; font-size: 20px; }}
      h2 {{ margin: 5px 0; font-size: 24px; }}
      table {{ margin: 5px 0; font-size: 14px; }}
      th, td {{ padding: 2px; }}
      #input-section {{ margin-bottom: 10px; }}
      #mobile-retry-btn {{ margin: 10px auto 5px auto; padding: 8px 20px; font-size: 18px; }}
  }}

  h2 {{ margin-top: 0; color: yellow; text-shadow: 2px 2px #f00; }}
  
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  th, td {{ border-bottom: 1px solid #555; padding: 5px; text-align: left; }}
  th {{ color: #aaa; }}
  .rank-col {{ width: 40px; text-align: center; }}
  .score-col {{ text-align: right; color: #0f0; }}
  
  #input-section {{ margin-bottom: 20px; display: none; }}
  input[type="text"] {{ padding: 5px; font-size: 16px; width: 150px; text-align: center; user-select: text; -webkit-user-select: text; }}
  button {{ padding: 5px 15px; font-size: 16px; cursor: pointer; background: #f00; color: white; border: none; font-weight: bold; }}
  
  #loading-msg {{ display: none; color: yellow; font-weight: bold; margin-top: 10px; animation: blink 1s infinite; }}
  .restart-msg {{ margin-top: 20px; font-size: 14px; color: #ccc; }}

  #mobile-retry-btn {{
      display: none; margin: 25px auto 10px auto; padding: 15px 40px; font-size: 24px;
      background: #00d2ff; border: 3px solid white; color: white; font-weight: bold;
      border-radius: 50px; cursor: pointer; animation: blink 2s infinite;
      box-shadow: 0 0 10px rgba(0, 210, 255, 0.8);
  }}
  
  #auto-restart-msg {{
      display: none; color: #00d2ff; margin-top: 20px; font-size: 18px; font-weight: bold; animation: blink 1s infinite;
  }}

  /* --- 縦画面警告 --- */
  #orientation-warning {{
      display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.95); z-index: 9999;
      flex-direction: column; justify-content: center; align-items: center;
      text-align: center; color: white;
  }}
  .rotate-icon {{ font-size: 60px; margin-bottom: 20px; }}
  .rotate-msg {{ font-size: 24px; font-weight: bold; animation: blinkRed 1s infinite; padding: 20px; }}

  /* --- モバイルコントローラー --- */
  #mobile-controls {{
    display: none; position: absolute; bottom: 0; left: 0; width: 100%; height: 100%; max-height: 200px;
    z-index: 100; pointer-events: none; justify-content: space-between; padding: 0 20px; box-sizing: border-box; align-items: flex-end; padding-bottom: 20px;
  }}

  @media (hover: none) and (pointer: coarse) {{
    #mobile-controls {{ display: flex; }}
    .restart-msg {{ display: none; }}
    #mobile-retry-btn {{ display: block !important; }}
  }}

  .joystick-area {{
      pointer-events: auto; width: 120px; height: 120px; margin-bottom: 20px; margin-left: 20px; position: relative;
      background: rgba(255, 255, 255, 0.1); border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 50%; touch-action: none;
  }}
  .joystick-knob {{
      width: 50px; height: 50px; background: rgba(0, 210, 255, 0.8); border-radius: 50%; position: absolute;
      top: 50%; left: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 10px rgba(0, 210, 255, 0.5); pointer-events: none;
  }}

  .action-btn-area {{ pointer-events: auto; margin-bottom: 40px; margin-right: 60px; }}
  .touch-btn {{
    width: 90px; height: 90px; border-radius: 50%; background: rgba(255, 255, 255, 0.2); border: 2px solid rgba(255, 255, 255, 0.6);
    color: white; font-size: 40px; display: flex; justify-content: center; align-items: center; touch-action: manipulation;
    user-select: none; -webkit-user-select: none; cursor: pointer; text-shadow: 1px 1px 2px black;
  }}
  .touch-btn:active {{ background: rgba(255, 255, 255, 0.5); }}

</style>
</head>
<body>

<div id="orientation-warning">
    <div class="rotate-icon">📱⟲</div>
    <div class="rotate-msg">Please Rotate Your Device<br>画面を横にしてください</div>
    <div style="margin-top:20px; color:#aaa;">Game Paused</div>
</div>

<div id="ui-layer">
    Score: <span id="score">0</span> | Level: <span id="level">1</span><br>
    Life: <span id="hearts">❤️❤️❤️</span>
    <div id="status-msg"></div>
</div>

<canvas id="gameCanvas" width="800" height="400"></canvas>

<div id="title-screen">
    <img id="title-img" class="title-img" src="https://raw.githubusercontent.com/m-fukuda-blip/game/main/game_title.png" alt="GAME TITLE">
    <div id="start-text" class="start-text">GAME START!</div>
</div>

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
        <table><thead><tr><th class="rank-col">#</th><th>Name</th><th class="score-col">Score</th></tr></thead><tbody id="ranking-body"></tbody></table>
    </div>
    <div class="restart-msg">Press 'R' to Restart</div>
    <button id="mobile-retry-btn" onclick="resetGame()">🔄 RETRY</button>
    <div id="auto-restart-msg"></div>
</div>

<div id="mobile-controls">
    <div id="joystick-area" class="joystick-area">
        <div id="joystick-knob" class="joystick-knob"></div>
    </div>
    <div class="action-btn-area">
        <div id="btn-jump" class="touch-btn" style="background: rgba(255, 200, 0, 0.4); width:100px; height:100px; font-size:50px;">▲</div>
    </div>
</div>

<script>
  document.addEventListener('contextmenu', event => event.preventDefault());
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  const isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (window.innerWidth < 800);
  let isPaused = false;
  const orientationWarning = document.getElementById('orientation-warning');

  function checkOrientationAndResize() {{
      if (isMobile) {{
          if (window.innerHeight > window.innerWidth) {{
              isPaused = true;
              orientationWarning.style.display = 'flex';
              canvas.width = window.innerWidth - 20;
              canvas.height = 400;
          }} else {{
              isPaused = false;
              orientationWarning.style.display = 'none';
              canvas.width = 800;
              canvas.height = 400;
          }}
      }} else {{
          canvas.width = 800;
          canvas.height = 400;
      }}
  }}
  window.addEventListener('resize', checkOrientationAndResize);
  checkOrientationAndResize();

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

  // ゲーム変数 (先に定義)
  const GRAVITY = 0.6, FRICTION = 0.8, BASE_GROUND_Y = 360;  
  let score = 0, level = 1, gameSpeed = 1.0, hp = 3, gameOver = false, isTitle = true; 
  let frameCount = 0, nextEnemySpawn = 0, nextItemSpawn = 0;
  let facingRight = true, isInvincible = false, invincibleTimer = 0, terrainSegments = [];
  let superMode = false, superModeTimer = 0, slowMode = false, slowModeTimer = 0;
  let floatingTexts = [], autoRestartTimer = null;
  let cameraX = 0, lastGeneratedX = 0;
  let platforms = [], checkpoints = [], nextCheckpointDist = 800 * 10; 
  
  let nextReverseEnemySpawn = 0;
  let speedUpShown = false;
  // ★追加: 王冠モード
  let crownMode = false;
  let crownModeTimer = 0;

  const BASE_BPM = 130, BASE_BEAT_TIME = 60 / BASE_BPM;

  function getSpeedMultiplier() {{
      if (score < 10000) {{ return 1.0 + (score / 10000) * 1.0; }}
      let base = 2.0; let extra = ((score - 10000) / 1000) * 0.02; return Math.min(4.0, base + extra);
  }}

  function getCurrentBeatTime() {{ return BASE_BEAT_TIME / getSpeedMultiplier(); }}

  const joystickArea = document.getElementById('joystick-area');
  const joystickKnob = document.getElementById('joystick-knob');
  let stickTouchId = null;

  if (joystickArea) {{
      const maxRadius = 40; const center = {{ x: 60, y: 60 }}; 
      joystickArea.addEventListener('touchstart', (e) => {{
          e.preventDefault(); const touch = e.changedTouches[0]; stickTouchId = touch.identifier; startBGM(); updateStick(touch);
      }}, {{passive: false}});
      joystickArea.addEventListener('touchmove', (e) => {{
          e.preventDefault();
          for (let i = 0; i < e.changedTouches.length; i++) {{ if (e.changedTouches[i].identifier === stickTouchId) {{ updateStick(e.changedTouches[i]); break; }} }}
      }}, {{passive: false}});
      const endStick = (e) => {{
          e.preventDefault();
          for (let i = 0; i < e.changedTouches.length; i++) {{
              if (e.changedTouches[i].identifier === stickTouchId) {{
                  stickTouchId = null; joystickKnob.style.transform = `translate(-50%, -50%) translate(0px, 0px)`;
                  keys.left = false; keys.right = false; keys.down = false; break;
              }}
          }}
      }};
      joystickArea.addEventListener('touchend', endStick); joystickArea.addEventListener('touchcancel', endStick);

      function updateStick(touch) {{
          const rect = joystickArea.getBoundingClientRect();
          let x = touch.clientX - rect.left - center.x; let y = touch.clientY - rect.top - center.y;
          const distance = Math.sqrt(x*x + y*y);
          if (distance > maxRadius) {{ const angle = Math.atan2(y, x); x = Math.cos(angle) * maxRadius; y = Math.sin(angle) * maxRadius; }}
          joystickKnob.style.transform = `translate(-50%, -50%) translate(${{x}}px, ${{y}}px)`;
          keys.left = false; keys.right = false; keys.down = false;
          if (distance > 10) {{ if (Math.abs(x) > Math.abs(y)) {{ if (x > 0) keys.right = true; else keys.left = true; }} else {{ if (y > 0) keys.down = true; }} }}
      }}
  }}
  
  const btnJump = document.getElementById('btn-jump');
  if(btnJump) {{ btnJump.addEventListener('touchstart', (e) => {{ e.preventDefault(); doJump(); }}); }}

  let screenShake = {{ x: 0, y: 0, duration: 0, intensity: 0 }};
  function addShake(intensity, duration) {{ screenShake.intensity = intensity; screenShake.duration = duration; }}
  function updateShake() {{
      if (screenShake.duration > 0) {{ screenShake.x = (Math.random() - 0.5) * screenShake.intensity; screenShake.y = (Math.random() - 0.5) * screenShake.intensity; screenShake.duration--; }} 
      else {{ screenShake.x = 0; screenShake.y = 0; }}
  }}

  let particles = [];
  function spawnParticles(x, y, color, count = 8) {{
      for (let i = 0; i < count; i++) {{ particles.push({{ x: x, y: y, vx: (Math.random() - 0.5) * 8, vy: (Math.random() - 0.5) * 8, life: 30 + Math.random() * 20, size: 4 + Math.random() * 4, color: color }}); }}
  }}
  function updateAndDrawParticles() {{
      for (let i = 0; i < particles.length; i++) {{
          let p = particles[i]; p.x += p.vx; p.y += p.vy; p.vy += 0.2; p.life--; p.size *= 0.95;
          if (p.life <= 0 || p.size < 0.5) {{ particles.splice(i, 1); i--; }}
      }}
  }}

  let audioCtx, isBgmPlaying = false, bgmTimeout = null, activeOscillators = [];
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
  
  // ★追加: Enemy3 アニメーション
  const enemy3Anim = [];
  for(let i=1; i<=2; i++) {{ enemy3Anim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/enemy3action${{i}}.png`, 52, 52)); }}

  const itemImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png", 45, 45);
  const capsuleImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/capsule.png", 45, 45);
  const mutekiImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/muteki.png", 45, 45);
  const jyamaImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/jyama.png", 45, 45);
  // ★追加: 王冠画像
  const crownImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/crown.png", 45, 45);
  
  const itemEffectAnim = [];
  for(let i=1; i<=3; i++) itemEffectAnim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/ItemAction0${{i}}.png`, 45, 45));

  const cloudImgWrappers = [];
  for(let i=1; i<=4; i++) cloudImgWrappers.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/cloud${{i}}.png`, 170, 120)); 

  const mountainImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/mountains.png", 3000, 200);
  const buildingImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/buildings.png", 3000, 200);

  // ★追加: 左からの敵生成 (Enemy3)
  function spawnReverseEnemy() {{
      let speedBase = 4; let multiplier = getSpeedMultiplier(); let finalSpeed = speedBase * multiplier;
      let ex = cameraX - 60; let ey = BASE_GROUND_Y - 52; 
      if (Math.random() < 0.5) ey = Math.random() * 200 + 50; // 50%で空中
      // typeを'enemy3'に
      enemies.push({{ x: ex, y: ey, width: 52, height: 52, dx: finalSpeed, dy: 0, type: 'enemy3', angle: 0, animIndex: 0, animTimer: 0, isReverse: true }});
  }}

  function spawnItemOnTerrain(tx, tw, ty) {{
      const r = Math.random(); let type = 'coin';
      if (r < 0.005) type = 'star'; 
      else if (r < 0.035) type = 'trap'; 
      else if (r < 0.045) type = 'heal'; 
      else if (r < 0.050) type = 'crown'; // ★追加: 王冠 (0.5%)
      else type = 'coin';

      let ix = tx + Math.random() * (tw - 50) + 25; let iy = ty - 45 - Math.random() * 100; 
      
      // 王冠は動く設定
      let dx = 0;
      if (type === 'crown') dx = -2; // プレイヤーに向かってくる

      items.push({{ x: ix, y: iy, width: 45, height: 45, dx: dx, isCollected: false, animIndex: 0, animTimer: 0, type: type }}); 
  }}
  
  // ... (中略) ...

  function resetGame() {{
    if (autoRestartTimer) clearInterval(autoRestartTimer); autoRestartMsg.style.display = 'none';
    player.x = 200; player.y = 0; player.dx = 0; player.dy = 0; cameraX = 0; lastGeneratedX = 0;
    player.state = 'idle'; player.animIndex = 0; player.animTimer = 0; player.idlePingPong = 1; player.combo = 0; player.jumpCount = 0;
    score = 0; level = 1; gameSpeed = 1.0; hp = 3;
    enemies = []; items = []; floatingTexts = []; particles = []; terrainSegments = []; platforms = []; checkpoints = []; nextCheckpointDist = 800 * 10;
    gameOver = false; frameCount = 0; isInvincible = false; nextEnemySpawn = 0; nextItemSpawn = 0;
    scoreEl.innerText = score; levelEl.innerText = level;
    superMode = false; superModeTimer = 0; slowMode = false; slowModeTimer = 0; statusMsgEl.innerText = "";
    speedUpShown = false; nextReverseEnemySpawn = 0;
    crownMode = false; crownModeTimer = 0; // ★追加

    isTitle = true; titleScreen.style.display = 'flex';
    titleImg.style.animation = 'none'; void titleImg.offsetWidth; titleImg.style.animation = 'slideUpFade 2s forwards';
    startText.style.opacity = '0'; startText.style.animation = 'none';
    setTimeout(() => {{ startText.style.animation = 'blinkFade 0.5s forwards'; setTimeout(() => {{ titleScreen.style.display = 'none'; isTitle = false; }}, 1000); }}, 2000);

    updateHearts(); initClouds(); checkOrientationAndResize(); updateTerrain(); 
    const startGround = getGroundYUnderPlayer(); const gY = startGround !== null ? startGround : BASE_GROUND_Y; 
    player.y = gY - player.height; overlay.style.display = 'none';
  }}

  function update() {{
    if (isPaused) return;
    if (gameOver && player.state !== 'dead') return; if (player.state === 'dead') return;
    if (isTitle) {{ updateClouds(); return; }}

    updateShake(); frameCount++; updateClouds();
    if (isInvincible) {{ invincibleTimer--; if (invincibleTimer <= 0) isInvincible = false; }}
    
    let statusText = "";
    if (superMode) {{ superModeTimer--; statusText += "🌟SUPER MODE! "; if (superModeTimer <= 0) superMode = false; }}
    if (slowMode) {{ slowModeTimer--; statusText += "🐢SLOW... "; if (slowModeTimer <= 0) slowMode = false; }}
    // ★追加: 王冠ステータス
    if (crownMode) {{ 
        crownModeTimer--; 
        statusText += "👑POINT x3 "; 
        if (crownModeTimer <= 0) crownMode = false; 
    }}

    statusMsgEl.innerText = statusText;
    if (superMode) statusMsgEl.style.color = "gold"; 
    else if (crownMode) statusMsgEl.style.color = "cyan"; // 王冠はシアン
    else if (slowMode) statusMsgEl.style.color = "violet"; 
    else statusMsgEl.innerText = "";
    
    if (score >= 10000 && !speedUpShown) {{
        speedUpShown = true;
        floatingTexts.push({{ x: canvas.width/2, y: canvas.height/2, text: "SPEED UP!!!", life: 120, dy: -0.5, size: 40, color: "red" }});
        playSound('gate');
    }}
    
    if (score >= 10000) {{
        if (frameCount >= nextReverseEnemySpawn) {{
            spawnReverseEnemy();
            nextReverseEnemySpawn = frameCount + Math.random() * 200 + 200;
        }}
    }}

    let currentSpeed = player.speed;
    if (slowMode) currentSpeed *= 0.5;

    if (player.state !== 'dead') {{
        if (player.state !== 'squat') {{
            if (keys.right) player.dx = currentSpeed; else if (keys.left) player.dx = -currentSpeed; else player.dx *= FRICTION;
        }} else {{ player.dx *= FRICTION; }}
        let nextX = player.x + player.dx; let checkX = player.dx > 0 ? nextX + player.width : nextX;
        let nextGroundY = getGroundYAtX(checkX); 
        if (nextGroundY !== null) {{ if (player.y + player.height > nextGroundY + 5) player.dx = 0; }}
        if (nextX < cameraX) {{ nextX = cameraX; player.dx = 0; }}
    }}

    player.x += player.dx; player.y += player.dy; player.dy += GRAVITY;
    let targetCameraX = player.x - 300; 
    if (targetCameraX < 0) targetCameraX = 0;
    if (targetCameraX > cameraX) cameraX = targetCameraX; 
    
    updateTerrain();
    const groundY = getGroundYUnderPlayer();
    if (groundY !== null) {{ 
        if (player.y + player.height >= groundY && player.dy >= 0) {{ player.y = groundY - player.height; player.dy = 0; player.jumping = false; player.combo = 0; player.jumpCount = 0; }} 
    }} else {{ 
        if (player.y > canvas.height) {{ if (isNaN(player.y)) player.y = 0; if (!gameOver) {{ hp = 0; updateHearts(); playSound('hit'); handleGameOver(); }} }} 
    }}
    
    updatePlayerAnimation();
    if (gameOver) return;

    updateAndDrawParticles();
    for (let i = 0; i < floatingTexts.length; i++) {{ let ft = floatingTexts[i]; ft.y += ft.dy; ft.life--; if (ft.life <= 0) {{ floatingTexts.splice(i, 1); i--; }} }}

    let playerHitH = player.height; let playerHitY = player.y;
    if (player.state === 'squat') {{ playerHitH = player.height / 2; playerHitY = player.y + player.height / 2; }}

    for (let i = 0; i < items.length; i++) {{ 
        let item = items[i]; 
        
        // ★追加: 王冠の動き (ふわふわ)
        if (item.type === 'crown') {{
            item.x += item.dx; // 横移動
            item.y += Math.sin(frameCount * 0.1) * 1.5; // 上下動
        }}

        if (item.x + item.width < cameraX - 100) {{ items.splice(i, 1); i--; continue; }}
        if (item.isCollected) {{
            if (item.type === 'coin') {{ item.animTimer++; if (item.animTimer > 5) {{ item.animIndex++; item.animTimer = 0; }} if (item.animIndex >= 3) {{ items.splice(i, 1); i--; }} }} 
            else {{ item.animTimer++; if (item.animTimer > 30) {{ items.splice(i, 1); i--; }} }}
        }} else {{
            if (item.type !== 'crown') item.x += item.dx; // 王冠以外は通常移動(dx=0)

            if (item.x + item.width < cameraX - 100) {{ items.splice(i, 1); i--; continue; }} 
            if (player.x < item.x + item.width && player.x + player.width > item.x && playerHitY < item.y + item.height && playerHitY + playerHitH > item.y) {{
                item.isCollected = true; item.animIndex = 0; item.animTimer = 0;
                if (item.type === 'coin') {{ score += 50; playSound('coin'); spawnParticles(item.x, item.y, 'gold', 5); }} 
                else if (item.type === 'heal') {{ hp = 3; updateHearts(); playSound('heal'); spawnParticles(item.x, item.y, 'pink', 8); }} 
                else if (item.type === 'star') {{ superMode = true; superModeTimer = 900; isInvincible = true; invincibleTimer = 900; slowMode = false; slowModeTimer = 0; playSound('powerup'); spawnParticles(item.x, item.y, 'yellow', 10); }} 
                else if (item.type === 'trap') {{ if (!superMode) {{ slowMode = true; slowModeTimer = 600; playSound('bad'); spawnParticles(item.x, item.y, 'purple', 8); }} }}
                // ★追加: 王冠取得処理
                else if (item.type === 'crown') {{
                    crownMode = true; crownModeTimer = 1800; // 30秒
                    playSound('powerup');
                    spawnParticles(item.x, item.y, 'cyan', 10);
                    floatingTexts.push({{ x: player.x, y: player.y - 20, text: "POINT x3!!!", life: 90, dy: -1.0, color: "cyan" }});
                }}

                scoreEl.innerText = score; updateLevel(); 
            }}
        }}
    }}

    let stompedThisFrame = false; 
    for (let i = 0; i < enemies.length; i++) {{ 
        let e = enemies[i]; 
        if (e.x + e.width < cameraX - 200 || e.x > cameraX + canvas.width + 200) {{ enemies.splice(i, 1); i--; continue; }}
        e.x += e.dx;
        e.animTimer++; if (e.animTimer > 10) {{ e.animIndex = (e.animIndex + 1) % 2; e.animTimer = 0; }}
        if (e.type === 'flying') {{ e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }} 

        if (player.x < e.x + e.width && player.x + player.width > e.x && playerHitY < e.y + e.height && playerHitY + playerHitH > e.y) {{ 
            const isStomp = (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) || stompedThisFrame || superMode;
            if (isStomp) {{ 
                enemies.splice(i, 1); i--; 
                if (!superMode) {{ player.dy = -10; stompedThisFrame = true; }}
                player.combo++; let multiplier = Math.pow(2, player.combo - 1); let bonusPoints = 100 * multiplier;
                
                // ★追加: 王冠ボーナス適用
                if (crownMode) {{
                    bonusPoints *= 3;
                    floatingTexts.push({{ x: player.x, y: player.y - 50, text: "CROWN BONUS", life: 60, dy: -2.0, color: "cyan", size: 18 }});
                }}

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

    for (let cp of checkpoints) {{
        if (!cp.passed && player.x > cp.x) {{
            cp.passed = true; score += 1500; scoreEl.innerText = score; playSound('gate');
            spawnParticles(player.x, player.y, 'cyan', 15);
            floatingTexts.push({{ x: player.x, y: player.y - 40, text: "CHECKPOINT! +1500", life: 90, dy: -0.5 }});
        }}
    }}
  }}

  // ... (draw関数内、敵とアイテムの描画部分を修正)
  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let skyColor; 
    if (score < 1000) skyColor = '#B0E0E6'; 
    else if (score < 3000) skyColor = '#FFDAB9'; 
    else if (score < 5000) skyColor = '#483D8B'; 
    else if (score < 10000) skyColor = '#6A5ACD'; 
    else skyColor = '#8B0000'; 

    ctx.fillStyle = skyColor; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.save(); ctx.translate(screenShake.x, screenShake.y);
    drawParallaxLayer(mountainImgWrapper, 0.1, canvas.height - 250); 
    for(let c of clouds) {{
        let wrapper = cloudImgWrappers[c.imgIndex]; let parallaxX = c.x - cameraX * 0.2; 
        if (wrapper && wrapper.ready && wrapper.img) ctx.drawImage(wrapper.img, parallaxX, c.y); 
        else {{ ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'; ctx.beginPath(); ctx.arc(parallaxX, c.y, 30, 0, Math.PI*2); ctx.fill(); }}
    }}
    drawParallaxLayer(buildingImgWrapper, 0.4, canvas.height - 220); 

    ctx.translate(-cameraX, 0); 
    for (let seg of terrainSegments) {{ ctx.fillStyle = '#654321'; ctx.fillRect(seg.x, seg.topY, seg.width, canvas.height - seg.topY); ctx.fillStyle = '#228B22'; ctx.fillRect(seg.x, seg.topY, seg.width, 10); }}
    ctx.fillStyle = '#999'; ctx.strokeStyle = '#555'; for (let p of platforms) {{ ctx.fillRect(p.x, p.y, p.width, p.height); ctx.strokeRect(p.x, p.y, p.width, p.height); }}
    ctx.strokeStyle = 'yellow'; ctx.lineWidth = 5;
    for (let cp of checkpoints) {{
        ctx.beginPath(); ctx.moveTo(cp.x, BASE_GROUND_Y); ctx.lineTo(cp.x, BASE_GROUND_Y - 150); ctx.arc(cp.x + 40, BASE_GROUND_Y - 150, 40, Math.PI, 0); ctx.lineTo(cp.x + 80, BASE_GROUND_Y); ctx.stroke();
        if (!cp.passed) {{ ctx.fillStyle = 'rgba(0, 255, 255, 0.3)'; ctx.fill(); }}
    }}

    for (let item of items) {{
        if (item.isCollected) {{
            if (item.type === 'coin') {{ let effectWrapper = itemEffectAnim[item.animIndex]; if(effectWrapper) drawObj(effectWrapper, item.x, item.y, item.width, item.height, 'yellow'); }}
            else {{
                ctx.save(); if (Math.floor(Date.now() / 50) % 2 === 0) ctx.globalAlpha = 0.2; else ctx.globalAlpha = 0.8;
                if (item.type === 'heal') drawObj(capsuleImgWrapper, item.x, item.y, item.width, item.height, 'pink'); 
                else if (item.type === 'star') drawObj(mutekiImgWrapper, item.x, item.y, item.width, item.height, 'yellow'); 
                else if (item.type === 'trap') drawObj(jyamaImgWrapper, item.x, item.y, item.width, item.height, 'purple');
                else if (item.type === 'crown') drawObj(crownImgWrapper, item.x, item.y, item.width, item.height, 'cyan'); // ★追加
                ctx.restore();
            }}
        }} else {{
            if (item.type === 'coin') drawObj(itemImgWrapper, item.x, item.y, item.width, item.height, 'gold'); 
            else if (item.type === 'heal') drawObj(capsuleImgWrapper, item.x, item.y, item.width, item.height, 'pink'); 
            else if (item.type === 'star') drawObj(mutekiImgWrapper, item.x, item.y, item.width, item.height, 'yellow'); 
            else if (item.type === 'trap') drawObj(jyamaImgWrapper, item.x, item.y, item.width, item.height, 'purple');
            else if (item.type === 'crown') drawObj(crownImgWrapper, item.x, item.y, item.width, item.height, 'cyan'); // ★追加
        }}
    }}

    for (let e of enemies) {{ 
        let animWrapper = null; 
        if (e.type === 'hard') {{ animWrapper = enemy2Anim[e.animIndex] || enemy2Anim[0]; drawObj(animWrapper, e.x, e.y, e.width, e.height, 'purple'); }} 
        else if (e.type === 'enemy3') {{ animWrapper = enemy3Anim[e.animIndex] || enemy3Anim[0]; drawObj(animWrapper, e.x, e.y, e.width, e.height, 'red'); }} // ★追加
        else {{ animWrapper = enemyAnim[e.animIndex] || enemyAnim[0]; drawObj(animWrapper, e.x, e.y, e.width, e.height, 'red'); }}
    }}
    
    // ... (以下略)
"""

components.html(game_html, height=550, scrolling=False)
