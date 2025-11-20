import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Graphic Platformer", layout="wide")

st.title("🎮 横スクロール：画像読み込みVer")
st.write("キャラクターや敵が画像（イラスト）になりました！")

# ゲームの本体
game_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background-color: #222; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; }
    canvas { background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); image-rendering: pixelated; } /* ドット絵くっきり */
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

    // --- 画像の読み込み設定 ---
    // ここを自分の画像のURL（GitHubのRaw URLなど）に書き換えると好きな画像になります。
    // 今回はすぐに動くように、簡易的なイラストデータを直接埋め込んでいます。
    
    // 1. プレイヤー画像 (青いスライム風)
    const playerImg = new Image();
    playerImg.src = "https://github.com/m-fukuda-blip/game/blob/5b031b559743d43b4f7add2fceb69416552bf412/player.png";

    // 2. 敵の画像 (赤いトゲトゲ)
    const enemyImg = new Image();
    enemyImg.src = "https://github.com/m-fukuda-blip/game/blob/803c7fc3898d42808aea5f4f864dbca0d471dd50/enemy.png";

    // 3. アイテム画像 (コイン)
    const itemImg = new Image();
    itemImg.src = "https://github.com/m-fukuda-blip/game/blob/8bb0035f7a315990508da2d24991a801aaae2806/coin.png";


    // ゲーム定数
    const GRAVITY = 0.6;
    const FRICTION = 0.8;
    const GROUND_Y = 360;

    let score = 0;
    let gameOver = false;
    let frameCount = 0;
    let nextEnemySpawn = 0;
    let nextItemSpawn = 0;
    let facingRight = true; // プレイヤーの向き

    const player = {
        x: 100, y: 300, width: 40, height: 40, // 画像に合わせてサイズ調整
        speed: 5, dx: 0, dy: 0, jumping: false
    };

    let enemies = [];
    let items = [];
    const keys = { right: false, left: false, up: false };

    document.addEventListener('keydown', (e) => {
        if (e.code === 'KeyD') { keys.right = true; facingRight = true; }
        if (e.code === 'KeyA') { keys.left = true; facingRight = false; }
        if (e.code === 'KeyW') {
            if (!player.jumping && !gameOver) {
                player.jumping = true;
                player.dy = -12;
            }
        }
        if (e.code === 'KeyR' && gameOver) resetGame();
    });

    document.addEventListener('keyup', (e) => {
        if (e.code === 'KeyD') keys.right = false;
        if (e.code === 'KeyA') keys.left = false;
    });

    function randomRange(min, max) { return Math.random() * (max - min) + min; }

    function spawnEnemy() {
        const type = Math.random() < 0.5 ? 'ground' : 'flying';
        let enemy = {
            x: canvas.width,
            y: 0,
            width: 35, height: 35,
            dx: -randomRange(2, 5),
            dy: 0,
            type: type,
            angle: 0
        };
        if (type === 'ground') enemy.y = GROUND_Y - enemy.height;
        else enemy.y = randomRange(200, 280);
        
        enemies.push(enemy);
        nextEnemySpawn = frameCount + randomRange(60, 120);
    }

    function spawnItem() {
        items.push({
            x: canvas.width,
            y: randomRange(150, 300),
            width: 30, height: 30,
            dx: -2
        });
        nextItemSpawn = frameCount + randomRange(40, 100);
    }

    function resetGame() {
        player.x = 100; player.y = 300; player.dx = 0; player.dy = 0;
        score = 0; enemies = []; items = [];
        gameOver = false; frameCount = 0;
        nextEnemySpawn = 50; nextItemSpawn = 30;
        scoreEl.innerText = score; msgEl.style.display = 'none';
        loop();
    }

    function update() {
        if (gameOver) return;
        frameCount++;

        if (keys.right) player.dx = player.speed;
        else if (keys.left) player.dx = -player.speed;
        else player.dx *= FRICTION;

        player.x += player.dx;
        player.y += player.dy;
        player.dy += GRAVITY;

        if (player.y + player.height > GROUND_Y) {
            player.y = GROUND_Y - player.height;
            player.dy = 0;
            player.jumping = false;
        }
        if (player.x < 0) player.x = 0;
        if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

        if (frameCount >= nextEnemySpawn) spawnEnemy();
        if (frameCount >= nextItemSpawn) spawnItem();

        // アイテム処理
        for (let i = 0; i < items.length; i++) {
            let item = items[i];
            item.x += item.dx;
            if (item.x + item.width < 0) { items.splice(i, 1); i--; continue; }

            if (player.x < item.x + item.width && player.x + player.width > item.x &&
                player.y < item.y + item.height && player.y + player.height > item.y) {
                score += 50; scoreEl.innerText = score;
                items.splice(i, 1); i--;
            }
        }

        // 敵処理
        for (let i = 0; i < enemies.length; i++) {
            let e = enemies[i];
            e.x += e.dx;
            if (e.type === 'flying') { e.angle += 0.1; e.y += Math.sin(e.angle) * 2; }
            if (e.x + e.width < 0) { enemies.splice(i, 1); i--; continue; }

            if (player.x < e.x + e.width && player.x + player.width > e.x &&
                player.y < e.y + e.height && player.y + player.height > e.y) {
                if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {
                    enemies.splice(i, 1); i--;
                    player.dy = -10; score += 100; scoreEl.innerText = score;
                } else {
                    gameOver = true; msgEl.style.display = 'block';
                }
            }
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 地面
        ctx.fillStyle = '#654321';
        ctx.fillRect(0, GROUND_Y, canvas.width, 40);
        ctx.fillStyle = '#228B22'; // 草の色を少しリアルに
        ctx.fillRect(0, GROUND_Y, canvas.width, 10);

        // アイテム描画 (drawImageを使用)
        for (let item of items) {
            ctx.drawImage(itemImg, item.x, item.y, item.width, item.height);
        }

        // 敵描画
        for (let e of enemies) {
            ctx.drawImage(enemyImg, e.x, e.y, e.width, e.height);
        }

        // プレイヤー描画 (向きに合わせて反転させる処理)
        ctx.save(); // 現在の描画状態を保存
        if (!facingRight) {
            // 左向きの場合：座標系を反転させる
            ctx.translate(player.x + player.width, player.y);
            ctx.scale(-1, 1);
            ctx.drawImage(playerImg, 0, 0, player.width, player.height);
        } else {
            // 右向き（通常）
            ctx.drawImage(playerImg, player.x, player.y, player.width, player.height);
        }
        ctx.restore(); // 描画状態を元に戻す
    }

    resetGame();

</script>
</body>
</html>
"""

components.html(game_html, height=500)
