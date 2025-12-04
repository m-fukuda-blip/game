import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Action Game with Ranking & Animation", layout="wide")
st.title("🎮 アクションゲーム：アニメーション実装版")
st.caption("機能：❤️ライフ制 / 🆙レベルアップ / ☁️背景 / 🔊効果音 / 🏆グローバルランキング / 🏃‍♂️アニメーション / 🎵加速するBGM / ✨アイテム効果 / 🧗‍♂️段差判定 / 💥コンボボーナス")
st.write("操作方法: **W** ジャンプ / **A** 左移動 / **D** 右移動 / **R** リセット / **F** 全画面")

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
  
  /* Canvas設定 */
  canvas {{ background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
  
  /* --- UIレイヤー --- */
  #ui-layer {{ position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; pointer-events: none; text-shadow: 1px 1px 0 #fff;}}
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
    padding: 30px; text-align: center; color: white; display: none; width: 400px; z-index: 20;
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
  const statusMsgEl = document.getElementById('status-msg');
  
  const overlay = document.getElementById('overlay');
  const inputSection = document.getElementById('input-section');
  const rankingBody = document.getElementById('ranking-body');
  const finalScoreDisplay = document.getElementById('final-score-display');
  const nameInput = document.getElementById('player-name');
  const submitBtn = document.getElementById('submit-btn');
  const loadingMsg = document.getElementById('loading-msg');
  const rankLoading = document.getElementById('rank-loading');

  const titleScreen = document.getElementById('title-screen');
  const titleImg = document.getElementById('title-img');
  const startText = document.getElementById('start-text');

  // ==========================================
  // BGM設定 (8bit Music)
  // ==========================================
  let audioCtx, isBgmPlaying = false;
  let bgmTimeout = null;
  let activeOscillators = [];
  const BASE_BPM = 130;
  const BASE_BEAT_TIME = 60 / BASE_BPM;

  const melody = [5,5,6,5,3,-1,3,5, 5,5,6,5,3,-1,3,2, 5,5,6,5,8,8,7,6, 6,5,3,3,-1,5,-1,-1];
  const scaleToFreq = (num) => {{ if(num < 0) return null; const scale = [261.63,293.66,329.63,349.23,392.00,440.00,493.88,523.25]; return scale[num-1]; }};

  function playNoiseForBGM(time, duration = 0.05, volume = 0.25){{
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const buffer = audioCtx.createBuffer(1, audioCtx.sampleRate * duration, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for(let i=0;i<data.length;i++) data[i] = (Math.random() * 2 - 1);
    const noise = audioCtx.createBufferSource();
    noise.buffer = buffer;
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(volume, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + duration);
    noise.connect(gain).connect(audioCtx.destination);
    noise.start(time);
    activeOscillators.push(noise);
  }}

  function playNoteForBGM(freq, time, duration){{
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    osc.type = "square";
    osc.frequency.value = freq;
    const gain = audioCtx.createGain();
    gain.gain.setValueAtTime(0.15, time); 
    gain.gain.exponentialRampToValueAtTime(0.01, time + duration);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start(time);
    osc.stop(time + duration);
    activeOscillators.push(osc);
  }}

  // ★ 修正2: BGM加速ロジック
  function getCurrentBeatTime() {{
      // スコア0で1倍、10000で4倍まで加速
      let multiplier = 1.0 + Math.min(score, 10000) / 10000 * 3.0; 
      return BASE_BEAT_TIME / multiplier;
  }}

  function playBGMLoop(){{
    if (!isBgmPlaying) return; 
    const start = audioCtx.currentTime;
    const currentBeat = getCurrentBeatTime(); // 動的にテンポ取得

    melody.forEach((note,i)=>{{
      const t = start + i * currentBeat;
      if(note > 0) playNoteForBGM(scaleToFreq(note), t, currentBeat);
      else playNoiseForBGM(t, 0.03, 0.1);
    }});
    
    // 次のループ予約時間も動的に変更
    bgmTimeout = setTimeout(playBGMLoop, melody.length * currentBeat * 1000);
  }}

  function startBGM() {{
    if (isBgmPlaying) return; 
    isBgmPlaying = true;
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    playBGMLoop();
  }}

  function stopBGM() {{
    isBgmPlaying = false;
    if (bgmTimeout) clearTimeout(bgmTimeout);
    activeOscillators.forEach(node => {{ try {{ node.stop(); }} catch(e) {{}} }});
    activeOscillators = []; 
  }}

  function playGameOverSound() {{
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth'; 
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    osc.frequency.setValueAtTime(800, now);
    osc.frequency.exponentialRampToValueAtTime(50, now + 0.8);
    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.8);
    osc.start(now);
    osc.stop(now + 0.8);
  }}

  // ==========================================
  // 画像読み込み (リサイズ関数を使用)
  // ==========================================
  function loadResized(src, w, h) {{
      const wrapper = {{ img: null, ready: false, error: false }};
      const img = new Image();
      img.crossOrigin = "Anonymous"; 
      img.src = src;
      img.onload = () => {{
          const offCanvas = document.createElement('canvas');
          offCanvas.width = w;
          offCanvas.height = h;
          const offCtx = offCanvas.getContext('2d');
          offCtx.drawImage(img, 0, 0, w, h);
          wrapper.img = offCanvas; wrapper.ready = true;
      }};
      img.onerror = () => {{ wrapper.error = true; }};
      return wrapper;
  }}

  const P_W = 40; const P_H = 40; 
  const playerAnim = {{ idle: [], run: [], jump: [], dead: null }};
  
  for(let i=1; i<=3; i++) {{ playerAnim.idle.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Taiki0${{i}}.png`, P_W, P_H)); }}
  for(let i=1; i<=3; i++) {{ playerAnim.run.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Run0${{i}}.png`, P_W, P_H)); }}
  for(let i=1; i<=3; i++) {{ playerAnim.jump.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Jump0${{i}}.png`, P_W, P_H)); }}
  playerAnim.dead = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/Dead.png", P_W, P_H);

  // 敵画像
  const enemyAnim = [];
  const enemy2Anim = [];
  for(let i=1; i<=2; i++) {{ enemyAnim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/EnemyAction0${{i}}.png`, 35, 35)); }}
  for(let i=1; i<=2; i++) {{ enemy2Anim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/Enemy2Action0${{i}}.png`, 35, 35)); }}
  
  // ★ アイテム画像
  const itemImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png", 30, 30);
  const capsuleImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/capsule.png", 30, 30);
  const mutekiImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/muteki.png", 30, 30);
  const jyamaImgWrapper = loadResized("https://raw.githubusercontent.com/m-fukuda-blip/game/main/jyama.png", 30, 30);
  
  const itemEffectAnim = [];
  for(let i=1; i<=3; i++) {{ itemEffectAnim.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/ItemAction0${{i}}.png`, 30, 30)); }}

  // ★ 雲画像
  const cloudImgWrappers = [];
  for(let i=1; i<=4; i++) {{ 
      cloudImgWrappers.push(loadResized(`https://raw.githubusercontent.com/m-fukuda-blip/game/main/cloud${{i}}.png`, 170, 120)); 
  }}

  // ゲーム変数
  const GRAVITY = 0.6;
  const FRICTION = 0.8;
  const BASE_GROUND_Y = 360;  
  
  let score = 0;
  let level = 1;
  let gameSpeed = 1.0;
  let hp = 3;
  let gameOver = false;
  let isTitle = true; 
  let frameCount = 0;
  let nextEnemySpawn = 0;
  let nextItemSpawn = 0;
  let facingRight = true;
  let isInvincible = false;
  let invincibleTimer = 0;
  let terrainSegments = [];
  
  // ★ 新しいステータス変数
  let superMode = false;       // 無敵スター状態
  let superModeTimer = 0;
  let slowMode = false;        // 速度低下状態
  let slowModeTimer = 0;
  
  // ★ ボーナステキスト配列
  let floatingTexts = [];

  const player = {{ 
      x: 100, y: 0, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false,
      state: 'idle', animIndex: 0, animTimer: 0, 
      animSpeedIdle: 15, animSpeedRun: 8, idlePingPong: 1,
      combo: 0 
  }};
  
  let enemies = [];
  let items = [];
  let clouds = [];
  const keys = {{ right: false, left: false, up: false }};

  // ==========================================
  // API設定
  // ==========================================
  const API_URL = "{GAS_API_URL}";
  let globalRankings = [];

  async function fetchRankings() {{
    try {{
        const response = await fetch(API_URL);
        const data = await response.json();
        return data;
    }} catch (e) {{ console.error(e); return []; }}
  }}

  async function sendScore(name, score) {{
    try {{
        await fetch(API_URL, {{ method: 'POST', body: JSON.stringify({{ name: name, score: score }}) }});
    }} catch (e) {{ console.error(e); }}
  }}

  fetchRankings().then(data => {{ globalRankings = data; }});

  function checkRankIn(currentScore) {{
    if (globalRankings.length < 10) return true;
    return currentScore > globalRankings[globalRankings.length - 1].score;
  }}

  async function submitScore() {{
    const name = nameInput.value.trim() || "NO NAME";
    nameInput.disabled = true; submitBtn.disabled = true; loadingMsg.style.display = 'block';
    await sendScore(name, score);
    globalRankings = await fetchRankings();
    loadingMsg.style.display = 'none'; nameInput.disabled = false; submitBtn.disabled = false;
    inputSection.style.display = 'none'; showRankingTable(globalRankings);
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
        }} else {{ row.innerHTML = `<td class="rank-col">${{i + 1}}</td><td>---</td><td class="score-col">0</td>`; }}
        rankingBody.appendChild(row);
    }}
  }}

  function handleGameOver() {{
    gameOver = true;
    player.state = 'dead'; 
    stopBGM(); playGameOverSound();
    overlay.style.display = 'block';
    finalScoreDisplay.innerText = "Final Score: " + score;
    nameInput.value = "";
    rankingBody.innerHTML = ""; rankLoading.style.display = "block";
    fetchRankings().then(data => {{
        globalRankings = data;
        rankLoading.style.display = "none";
        showRankingTable(globalRankings);
        if (score > 0 && checkRankIn(score)) {{ inputSection.style.display = 'block'; nameInput.focus(); }} 
        else {{ inputSection.style.display = 'none'; }}
    }});
  }}

  function playSound(type) {{
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
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
    }} else if (type === 'heal') {{
        osc.type = 'sine'; osc.frequency.setValueAtTime(400, now); osc.frequency.linearRampToValueAtTime(800, now + 0.2);
        gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.3);
        osc.start(now); osc.stop(now + 0.3);
    }} else if (type === 'powerup') {{
        osc.type = 'square'; osc.frequency.setValueAtTime(440, now); osc.frequency.setValueAtTime(880, now + 0.1);
        gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.5);
        osc.start(now); osc.stop(now + 0.5);
    }} else if (type === 'bad') {{
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(300, now); osc.frequency.linearRampToValueAtTime(150, now + 0.3);
        gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.3);
        osc.start(now); osc.stop(now + 0.3);
    }}
  }}

  document.addEventListener('keydown', (e) => {{
    if (document.activeElement === nameInput) {{ if (e.key === 'Enter' && !submitBtn.disabled) submitScore(); return; }}
    if (player.state === 'dead' && e.code !== 'KeyR') return;
    if (e.code === 'KeyF') {{ if (!document.fullscreenElement) document.documentElement.requestFullscreen(); else if (document.exitFullscreen) document.exitFullscreen(); }}
    if (['KeyW', 'KeyA', 'KeyD', 'KeyR', 'KeyF'].includes(e.code)) {{ e.preventDefault(); }}
    if (e.code === 'KeyD') {{ keys.right = true; facingRight = true; startBGM(); }} 
    if (e.code === 'KeyA') {{ keys.left = true; facingRight = false; startBGM(); }} 
    if (e.code === 'KeyW') {{ if (!player.jumping && !gameOver && !isTitle) {{ player.jumping = true; player.dy = -12; playSound('jump'); startBGM(); }} }}
    if (e.code === 'KeyR' && gameOver) resetGame();
  }});

  document.addEventListener('keyup', (e) => {{
    if (e.code === 'KeyD') keys.right = false;
    if (e.code === 'KeyA') keys.left = false;
  }});

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
    if (score >= 2000 && Math.random() < 0.3) {{ type = 'hard'; speedBase = 5; }}
    let enemy = {{ x: canvas.width, y: 0, width: 35, height: 35, dx: -(speedBase * gameSpeed), dy: 0, type: type, angle: 0, animIndex: 0, animTimer: 0 }};
    
    // ★ 修正3: 敵の出現位置制限
    const SAFE_Y_LIMIT = BASE_GROUND_Y - 40; // これより下(Yが大きい)場所には出さない
    
    if (type === 'ground' || type === 'hard') {{ 
        const gY = getGroundYAtX(enemy.x); 
        // 地面があり、かつ地面の高さが安全ラインより上(Yが小さい)場合のみ地面設置
        if (gY !== null && gY <= SAFE_Y_LIMIT) {{ 
            enemy.y = gY - enemy.height; 
        }} else {{ 
            // 地面が低すぎる場合は、空中の安全圏に出現させる
            enemy.type = 'flying'; 
            enemy.y = Math.random() * (SAFE_Y_LIMIT - 200 - enemy.height) + 200; 
        }} 
    }} else {{ 
        enemy.y = Math.random() * (SAFE_Y_LIMIT - 200 - enemy.height) + 200;
    }}
    enemies.push(enemy); nextEnemySpawn = frameCount + Math.random() * (Math.max(20, 60 - (level * 5))) + Math.max(20, 60 - (level * 5));
  }}
  
  function spawnItem() {{ 
    // ★ アイテム出現率の調整
    const r = Math.random();
    let type = 'coin';
    if (r < 0.005) type = 'star';
    else if (r < 0.035) type = 'trap';
    else if (r < 0.045) type = 'heal';
    else type = 'coin';

    items.push({{ 
        x: canvas.width, y: Math.random() * 150 + 150, width: 30, height: 30, dx: -2,
        isCollected: false, animIndex: 0, animTimer: 0,
        type: type 
    }}); 
    nextItemSpawn = frameCount + Math.random() * 60 + 40; 
  }}
  
  // ★ 雲の初期化
  function initClouds() {{
    clouds = [];
    for(let i=0; i<5; i++) {{
        clouds.push({{
            x: Math.random() * canvas.width, 
            y: Math.random() * 150, 
            speed: Math.random() * 0.5 + 0.2,
            imgIndex: Math.floor(Math.random() * 4) 
        }});
    }}
  }}

  // ★ 雲の更新
  function updateClouds() {{
    for(let c of clouds) {{
        c.x -= c.speed;
        if(c.x < -150) {{ 
            c.x = canvas.width; 
            c.y = Math.random() * 150; 
            c.imgIndex = Math.floor(Math.random() * 4);
        }}
    }}
  }}

  function updateLevel() {{ const newLevel = Math.floor(score / 500) + 1; if (newLevel > level) {{ level = newLevel; gameSpeed = 1.0 + (level * 0.1); levelEl.innerText = level; if(hp < 3) {{ hp++; updateHearts(); }} }} }}

  function updateHearts() {{ let h = ""; for(let i=0; i<hp; i++) h += "❤️"; heartsEl.innerText = h; }}

  function resetGame() {{
    player.x = 100; player.y = 0; player.dx = 0; player.dy = 0;
    player.state = 'idle'; player.animIndex = 0; player.animTimer = 0; player.idlePingPong = 1;
    player.combo = 0; // コンボリセット
    score = 0; level = 1; gameSpeed = 1.0; hp = 3;
    enemies = []; items = []; floatingTexts = []; // リセット
    gameOver = false; frameCount = 0;
    isInvincible = false; nextEnemySpawn = 50; nextItemSpawn = 30;
    scoreEl.innerText = score; levelEl.innerText = level;
    
    superMode = false; superModeTimer = 0;
    slowMode = false; slowModeTimer = 0;
    statusMsgEl.innerText = "";

    isTitle = true; titleScreen.style.display = 'flex';
    titleImg.style.animation = 'none'; void titleImg.offsetWidth; titleImg.style.animation = 'slideUpFade 2s forwards';
    startText.style.opacity = '0'; startText.style.animation = 'none';
    setTimeout(() => {{ startText.style.animation = 'blinkFade 0.5s forwards'; setTimeout(() => {{ titleScreen.style.display = 'none'; isTitle = false; }}, 1000); }}, 2000);

    updateHearts(); initClouds(); generateCourse();
    const startGround = getGroundYUnderPlayer(); const gY = startGround !== null ? startGround : BASE_GROUND_Y; player.y = gY - player.height;
    overlay.style.display = 'none';
  }}

  function updatePlayerAnimation() {{
    const prevState = player.state;
    if (hp <= 0) player.state = 'dead';
    else if (player.jumping) player.state = 'jump';
    else if (keys.right || keys.left) player.state = 'run';
    else player.state = 'idle';

    if (player.state !== prevState) {{ player.animTimer = 0; player.animIndex = 0; player.idlePingPong = 1; }}
    player.animTimer++;
    switch (player.state) {{
        case 'idle': if (player.animTimer > player.animSpeedIdle) {{ player.animIndex += player.idlePingPong; if (player.animIndex >= 2) player.idlePingPong = -1; if (player.animIndex <= 0) player.idlePingPong = 1; player.animTimer = 0; }} break;
        case 'run': if (player.animTimer > player.animSpeedRun) {{ player.animIndex = (player.animIndex + 1) % 3; player.animTimer = 0; }} break;
        case 'jump': if (player.dy < -5) player.animIndex = 0; else if (player.dy < 0) player.animIndex = 1; else if (player.dy < 5) player.animIndex = 2; else player.animIndex = 1; break;
        case 'dead': player.animIndex = 0; break;
    }}
  }}

  function update() {{
    if (gameOver && player.state !== 'dead') return; if (player.state === 'dead') return;
    if (isTitle) {{ updateClouds(); return; }}

    frameCount++; updateClouds();
    if (isInvincible) {{ invincibleTimer--; if (invincibleTimer <= 0) isInvincible = false; }}
    
    // ★ ステータス効果のタイマー更新
    let statusText = "";
    if (superMode) {{
        superModeTimer--;
        statusText += "🌟SUPER MODE! ";
        if (superModeTimer <= 0) superMode = false;
    }}
    if (slowMode) {{
        slowModeTimer--;
        statusText += "🐢SLOW... ";
        if (slowModeTimer <= 0) slowMode = false;
    }}
    statusMsgEl.innerText = statusText;
    if (superMode) statusMsgEl.style.color = "gold";
    else if (slowMode) statusMsgEl.style.color = "violet";
    else statusMsgEl.innerText = "";

    // ★ 移動処理（Slow状態なら速度半減）
    let currentSpeed = player.speed;
    if (slowMode) currentSpeed *= 0.5;

    // ★ 修正1: 段差の壁判定（ジャンプしないと登れないようにする）
    if (player.state !== 'dead') {{
        // キー入力による加速
        if (keys.right) player.dx = currentSpeed;
        else if (keys.left) player.dx = -currentSpeed;
        else player.dx *= FRICTION;

        // 移動先の座標計算
        let nextX = player.x + player.dx;
        let checkX = player.dx > 0 ? nextX + player.width : nextX;
        let nextGroundY = getGroundYAtX(checkX); // 移動先の地面高さ

        if (nextGroundY !== null) {{
            // 足元の高さより、移動先の地面が高い（数値が小さい）場合
            // 許容範囲（5px）を超えて高い場合は、移動をブロック
            if (player.y + player.height > nextGroundY + 5) {{
                player.dx = 0; // 進めない
                // nextXは更新しない（現在の位置を維持）
            }}
        }}
    }}

    player.x += player.dx; player.y += player.dy; player.dy += GRAVITY;
    if (player.x < 0) player.x = 0;
    if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

    const groundY = getGroundYUnderPlayer();
    if (groundY !== null) {{ 
        if (player.y + player.height >= groundY && player.dy >= 0) {{ 
            player.y = groundY - player.height; player.dy = 0; player.jumping = false; 
            // ★着地したらコンボリセット
            player.combo = 0;
        }} 
    }} 
    else {{ if (player.y > canvas.height) {{ if (!gameOver) {{ hp = 0; updateHearts(); playSound('hit'); handleGameOver(); }} }} }}
    
    updatePlayerAnimation();
    if (gameOver) return;

    if (frameCount >= nextEnemySpawn) spawnEnemy();
    if (frameCount >= nextItemSpawn) spawnItem();

    // ★ フローティングテキスト更新
    for (let i = 0; i < floatingTexts.length; i++) {{
        let ft = floatingTexts[i];
        ft.y += ft.dy;
        ft.life--;
        if (ft.life <= 0) {{
            floatingTexts.splice(i, 1);
            i--;
        }}
    }}

    // ★ アイテム更新（効果の適用とアニメーション分岐）
    for (let i = 0; i < items.length; i++) {{ 
        let item = items[i]; 
        
        if (item.isCollected) {{
            if (item.type === 'coin') {{
                item.animTimer++;
                if (item.animTimer > 5) {{ item.animIndex++; item.animTimer = 0; }}
                if (item.animIndex >= 3) {{ items.splice(i, 1); i--; }}
            }} else {{
                item.animTimer++;
                if (item.animTimer > 30) {{ 
                    items.splice(i, 1);
                    i--;
                }}
            }}
        }} else {{
            item.x += item.dx;
            if (item.x + item.width < 0) {{ items.splice(i, 1); i--; continue; }} 
            if (player.x < item.x + item.width && player.x + player.width > item.x && player.y < item.y + item.height && player.y + player.height > item.y) {{
                item.isCollected = true; item.animIndex = 0; item.animTimer = 0;
                
                if (item.type === 'coin') {{
                    score += 50; playSound('coin');
                }} else if (item.type === 'heal') {{
                    hp = 3; updateHearts(); playSound('heal');
                }} else if (item.type === 'star') {{
                    // ★ 修正1: 無敵時間を900 (15秒) に短縮
                    superMode = true; superModeTimer = 900; 
                    isInvincible = true; invincibleTimer = 900;
                    slowMode = false; slowModeTimer = 0;
                    playSound('powerup');
                }} else if (item.type === 'trap') {{
                    if (!superMode) {{
                        slowMode = true; slowModeTimer = 600; 
                        playSound('bad');
                    }}
                }}
                
                scoreEl.innerText = score; updateLevel(); 
            }}
        }}
    }}

    // ★ 敵更新（無敵アタック判定）
    let stompedThisFrame = false; 
    for (let i = 0; i < enemies.length; i++) {{ 
        let e = enemies[i]; e.x += e.dx;
        e.animTimer++; if (e.animTimer > 10) {{ e.animIndex = (e.animIndex + 1) % 2; e.animTimer = 0; }}
        if (e.type === 'flying') {{ e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }} 
        if (e.x + e.width < 0) {{ enemies.splice(i, 1); i--; continue; }} 

        if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {{ 
            const isStomp = (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) || stompedThisFrame || superMode;

            if (isStomp) {{ 
                enemies.splice(i, 1); i--; 
                
                if (!superMode) {{
                    player.dy = -10; 
                    stompedThisFrame = true; 
                }}
                
                // ★ 修正2: 連続踏みつけボーナス計算
                player.combo++;
                let multiplier = Math.pow(2, player.combo - 1); // 1, 2, 4, 8...
                let bonusPoints = 100 * multiplier;
                score += bonusPoints; 
                scoreEl.innerText = score; 
                playSound('coin'); updateLevel(); 

                // ★ ボーナステキスト表示 (2倍以上で表示)
                if (multiplier > 1) {{
                    floatingTexts.push({{
                        x: player.x,
                        y: player.y - 20,
                        text: "BONUS x" + multiplier,
                        life: 60,
                        dy: -1.5
                    }});
                }}

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

  function drawObj(wrapper, x, y, w, h, fallbackColor) {{
    if (wrapper && wrapper.ready && wrapper.img) ctx.drawImage(wrapper.img, x, y, w, h);
    else {{ ctx.fillStyle = fallbackColor; ctx.fillRect(x, y, w, h); }}
  }}

  function draw() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#87CEEB'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // ★ 雲描画 (画像を使用)
    for(let c of clouds) {{
        let wrapper = cloudImgWrappers[c.imgIndex];
        if (wrapper && wrapper.ready && wrapper.img) {{
             ctx.drawImage(wrapper.img, c.x, c.y); 
        }} else {{
             ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
             ctx.beginPath(); ctx.arc(c.x, c.y, 30, 0, Math.PI*2); ctx.fill();
        }}
    }}

    for (let seg of terrainSegments) {{ ctx.fillStyle = '#654321'; ctx.fillRect(seg.x, seg.topY, seg.width, canvas.height - seg.topY); ctx.fillStyle = '#228B22'; ctx.fillRect(seg.x, seg.topY, seg.width, 10); }}
    
    // ★ アイテム描画（種類別）
    for (let item of items) {{
        if (item.isCollected) {{
            // 取得後
            if (item.type === 'coin') {{
                let effectWrapper = itemEffectAnim[item.animIndex];
                if(effectWrapper) drawObj(effectWrapper, item.x, item.y, item.width, item.height, 'yellow');
            }} else {{
                ctx.save();
                if (Math.floor(Date.now() / 50) % 2 === 0) ctx.globalAlpha = 0.2;
                else ctx.globalAlpha = 0.8;
                
                if (item.type === 'heal') drawObj(capsuleImgWrapper, item.x, item.y, item.width, item.height, 'pink');
                else if (item.type === 'star') drawObj(mutekiImgWrapper, item.x, item.y, item.width, item.height, 'yellow');
                else if (item.type === 'trap') drawObj(jyamaImgWrapper, item.x, item.y, item.width, item.height, 'purple');
                
                ctx.restore();
            }}
        }} else {{
            // 通常時
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
    if (superMode) {{
        if (Math.floor(Date.now() / 50) % 2 === 0) {{ ctx.globalAlpha = 0.8; ctx.filter = 'brightness(1.5) drop-shadow(0 0 5px gold)'; }}
    }} else if (slowMode) {{
        ctx.filter = 'hue-rotate(270deg)';
    }} else if (isInvincible) {{
        if (Math.floor(Date.now() / 100) % 2 === 0) ctx.globalAlpha = 0.5;
    }}
    
    let currentWrapper = null;
    if (player.state === 'dead') currentWrapper = playerAnim.dead;
    else currentWrapper = playerAnim[player.state][player.animIndex];

    if (!facingRight) {{ ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); drawObj(currentWrapper, 0, 0, player.width, player.height, 'blue'); }} 
    else {{ drawObj(currentWrapper, player.x, player.y, player.width, player.height, 'blue'); }}
    ctx.restore();

    // ★ ボーナステキスト描画
    ctx.fillStyle = "yellow";
    ctx.font = "bold 20px Courier New";
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;
    for (let ft of floatingTexts) {{
        ctx.strokeText(ft.text, ft.x, ft.y);
        ctx.fillText(ft.text, ft.x, ft.y);
    }}
  }}

  function loop() {{
    update(); draw(); requestAnimationFrame(loop);
  }}

  resetGame(); loop(); 

</script>
</body>
</html>
"""

components.html(game_html, height=550, scrolling=False)
