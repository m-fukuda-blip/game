import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Simple Platformer", layout="wide")

st.title("🕹️ 横スクロールアクションゲーム")
st.write("操作方法: **W**: ジャンプ, **A**: 左移動, **D**: 右移動")
st.write("敵（赤色）の上からジャンプして踏むと倒せます！")

# ゲームの本体（HTML/JS/CSS）
game_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background-color: #222; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
    canvas { background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
    #score-board { position: absolute; top: 20px; left: 20px; font-size: 24px; font-weight: bold; color: black; }
    #message { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 40px; color: red; font-weight: bold; display: none; text-shadow: 2px 2px white; }
</style>
</head>
<body>

<div id="score-board">Score: <span id="score">0</span></div>
<div id="message">GAME OVER<br><span style="font-size:20px; color:black">Press 'R' to Restart</span></div>
<canvas id="gameCanvas" width="800" height="400"></canvas>

<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const scoreEl = document.getElementById('score');
    const msgEl = document.getElementById('message');

    // ゲーム設定
    const gravity = 0.6;
    const friction = 0.8;
    let score = 0;
    let gameOver = false;

    // プレイヤー設定
    const player = {
        x: 100,
        y: 300,
        width: 30,
        height: 30,
        speed: 5,
        dx: 0,
        dy: 0,
        jumping: false,
        color: '#3333ff' // 青色
    };

    // 敵の設定
    let enemies = [];
    const enemySpeed = 2;
    let frameCount = 0;

    // キー入力管理
    const keys = {
        right: false,
        left: false,
        up: false
    };

    document.addEventListener('keydown', (e) => {
        if (e.code === 'KeyD') keys.right = true;
        if (e.code === 'KeyA') keys.left = true;
        if (e.code === 'KeyW') {
            if (!player.jumping && !gameOver) {
                player.jumping = true;
                player.dy = -12; // ジャンプ力
            }
        }
        if (e.code === 'KeyR' && gameOver) resetGame();
    });

    document.addEventListener('keyup', (e) => {
        if (e.code === 'KeyD') keys.right = false;
        if (e.code === 'KeyA') keys.left = false;
    });

    function spawnEnemy() {
        // 画面右外から敵を生成
        enemies.push({
            x: canvas.width,
            y: 330, // 地面の上
            width: 30,
            height: 30,
            dx: -enemySpeed,
            color: '#ff3333', // 赤色
            alive: true
        });
    }

    function resetGame() {
        player.x = 100;
        player.y = 300;
        player.dx = 0;
        player.dy = 0;
        score = 0;
        enemies = [];
        gameOver = false;
        scoreEl.innerText = score;
        msgEl.style.display = 'none';
        loop();
    }

    function update() {
        if (gameOver) return;

        // プレイヤーの移動
        if (keys.right) player.dx = player.speed;
        else if (keys.left) player.dx = -player.speed;
        else player.dx *= friction;

        player.x += player.dx;
        player.y += player.dy;

        // 重力
        player.dy += gravity;

        // 床との当たり判定
        if (player.y + player.height > 360) {
            player.y = 360 - player.height;
            player.dy = 0;
            player.jumping = false;
        }

        // 壁との当たり判定
        if (player.x < 0) player.x = 0;
        if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

        // 敵の生成と管理
        frameCount++;
        if (frameCount % 120 === 0) spawnEnemy(); // 2秒ごとに生成

        for (let i = 0; i < enemies.length; i++) {
            let e = enemies[i];
            e.x += e.dx;

            // 画面外に出たら削除
            if (e.x + e.width < 0) {
                enemies.splice(i, 1);
                i--;
                continue;
            }

            // 当たり判定（AABB）
            if (
                player.x < e.x + e.width &&
                player.x + player.width > e.x &&
                player.y < e.y + e.height &&
                player.y + player.height > e.y
            ) {
                // 上から踏んだか判定 (プレイヤーが落下中 かつ 敵の上にいる)
                if (player.dy > 0 && player.y + player.height - e.dy < e.y + e.height / 2) {
                    // 敵を倒した
                    enemies.splice(i, 1);
                    i--;
                    player.dy = -8; // 踏んで少し跳ねる
                    score += 100;
                    scoreEl.innerText = score;
                } else {
                    // ぶつかってゲームオーバー
                    gameOver = true;
                    msgEl.style.display = 'block';
                }
            }
        }
    }

    function draw() {
        // 背景クリア
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 地面を描画
        ctx.fillStyle = '#654321';
        ctx.fillRect(0, 360, canvas.width, 40);

        // 草を描画
        ctx.fillStyle = '#32CD32';
        ctx.fillRect(0, 360, canvas.width, 10);

        // プレイヤーを描画
        ctx.fillStyle = player.color;
        ctx.fillRect(player.x, player.y, player.width, player.height);

        // 敵を描画
        for (let e of enemies) {
            ctx.fillStyle = e.color;
            ctx.fillRect(e.x, e.y, e.width, e.height);
        }
    }

    function loop() {
        update();
        draw();
        if (!gameOver) requestAnimationFrame(loop);
    }

    // ゲーム開始
    loop();

</script>
</body>
</html>
"""

# StreamlitにHTMLコンポーネントとして埋め込む
components.html(game_html, height=500)
