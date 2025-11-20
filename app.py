import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Fixed Game", layout="wide")
st.title("🎮 修正版：横スクロールアクション")
st.write("もし画像が表示されない場合は、色付きの四角形が表示されます。")

game_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background-color: #222; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; }
    canvas { background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); image-rendering: pixelated; }
    #ui-layer { position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; pointer-events: none;}
    #message { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 40px; color: red; font-weight: bold; display: none; text-shadow: 2px 2px white; text-align: center; }
</style>
</head>
<body>

<div id="ui-layer">Score: <span id="score">0</span></div>
<div id="message">GAME OVER<br><span style="font-size:20px; color:black">Press 'R' to Restart</span></div>
<canvas id="gameCanvas" width="800" height="400"></canvas>

<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const scoreEl = document.getElementById('score');
    const msgEl = document.getElementById('message');

    // ==========================================
    // 画像の設定 (ここを修正)
    // ==========================================
    
    // 1. プレイヤー画像 (Base64データ)
    const playerImg = new Image();
    playerImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/player.png";

    // 2. 敵の画像
    const enemyImg = new Image();
    enemyImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/enemy.png";

    // 3. アイテム画像
    const itemImg = new Image();
    itemImg.src = "https://raw.githubusercontent.com/m-fukuda-blip/game/main/coin.png";

    // ==========================================

    const GRAVITY = 0.6;
    const FRICTION = 0.8;
    const GROUND_Y = 360;

    let score = 0;
    let gameOver = false;
    let frameCount = 0;
    let nextEnemySpawn = 0;
    let nextItemSpawn = 0;
    let facingRight = true;

    const player = { x: 100, y: 300, width: 40, height: 40, speed: 5, dx: 0, dy: 0, jumping: false };
    let enemies = [];
    let items = [];
    const keys = { right: false, left: false, up: false };

    document.addEventListener('keydown', (e) => {
        if (e.code === 'KeyD') { keys.right = true; facingRight = true; }
        if (e.code === 'KeyA') { keys.left = true; facingRight = false; }
        if (e.code === 'KeyW') { if (!player.jumping && !gameOver) { player.jumping = true; player.dy = -12; } }
        if (e.code === 'KeyR' && gameOver) resetGame();
    });

    document.addEventListener('keyup', (e) => {
        if (e.code === 'KeyD') keys.right = false;
        if (e.code === 'KeyA') keys.left = false;
    });

    function spawnEnemy() {
        const type = Math.random() < 0.5 ? 'ground' : 'flying';
        let enemy = {
            x: canvas.width, y: 0, width: 35, height: 35, dx: -(Math.random() * 3 + 2), dy: 0, type: type, angle: 0
        };
        if (type === 'ground') enemy.y = GROUND_Y - enemy.height;
        else enemy.y = Math.random() * 80 + 200;
        enemies.push(enemy);
        nextEnemySpawn = frameCount + Math.random() * 60 + 60;
    }

    function spawnItem() {
        items.push({ x: canvas.width, y: Math.random() * 150 + 150, width: 30, height: 30, dx: -2 });
        nextItemSpawn = frameCount + Math.random() * 60 + 40;
    }

    function resetGame() {
        player.x = 100; player.y = 300; player.dx = 0; player.dy = 0;
        score = 0; enemies = []; items = []; gameOver = false; frameCount = 0;
        nextEnemySpawn = 50; nextItemSpawn = 30; scoreEl.innerText = score;
        msgEl.style.display = 'none';
        loop();
    }

    function update() {
        if (gameOver) return;
        frameCount++;

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
                score += 50; scoreEl.innerText = score; items.splice(i, 1); i--;
            }
        }

        for (let i = 0; i < enemies.length; i++) {
            let e = enemies[i]; e.x += e.dx;
            if (e.type === 'flying') { e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }
            if (e.x + e.width < 0) { enemies.splice(i, 1); i--; continue; }
            if (player.x < e.x + e.width && player.x + player.width > e.x && player.y < e.y + e.height && player.y + player.height > e.y) {
                if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {
                    enemies.splice(i, 1); i--; player.dy = -10; score += 100; scoreEl.innerText = score;
                } else {
                    gameOver = true; msgEl.style.display = 'block';
                }
            }
        }
    }

    // 安全な描画関数（この関数は消さないでください！）
    function drawObj(img, x, y, w, h, fallbackColor) {
        // 画像が読み込み完了(complete) かつ サイズが0じゃない場合のみ描画
        if (img.complete && img.naturalHeight !== 0) {
            ctx.drawImage(img, x, y, w, h);
        } else {
            // まだ読み込み中なら四角形を表示（これでエラー落ちを防ぐ）
            ctx.fillStyle = fallbackColor;
            ctx.fillRect(x, y, w, h);
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#654321'; ctx.fillRect(0, GROUND_Y, canvas.width, 40);
        ctx.fillStyle = '#228B22'; ctx.fillRect(0, GROUND_Y, canvas.width, 10);

        // 安全な描画関数を使用
        for (let item of items) drawObj(itemImg, item.x, item.y, item.width, item.height, 'gold');
        for (let e of enemies) drawObj(enemyImg, e.x, e.y, e.width, e.height, 'red');

        ctx.save();
        if (!facingRight) { ctx.translate(player.x + player.width, player.y); ctx.scale(-1, 1); drawObj(playerImg, 0, 0, player.width, player.height, 'blue'); }
        else { drawObj(playerImg, player.x, player.y, player.width, player.height, 'blue'); }
        ctx.restore();
    }

    function loop() {
        update();
        draw();
        if (!gameOver) requestAnimationFrame(loop);
    }

    // 画像の読み込みを待たずにスタート（失敗時は四角形で動く）
    resetGame();

</script>
</body>
</html>
"""

components.html(game_html, height=500)
