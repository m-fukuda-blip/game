import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Advanced Platformer", layout="wide")

st.title("🏃‍♂️ 横スクロールアクション：コインを集めろ！")
st.write("操作方法: **W**: ジャンプ, **A**: 左移動, **D**: 右移動")
st.write("🔴 **敵**: 上から踏んで倒せます（空飛ぶ敵に注意！）")
st.write("🟡 **コイン**: 取るとスコアアップ！")

# ゲームの本体（HTML/JS/CSS）
game_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background-color: #222; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 80vh; }
    canvas { background-color: #87CEEB; border: 4px solid #fff; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
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

    // ゲーム定数
    const GRAVITY = 0.6;
    const FRICTION = 0.8;
    const GROUND_Y = 360;

    // ゲーム状態
    let score = 0;
    let gameOver = false;
    let frameCount = 0;
    
    // スポーン管理用
    let nextEnemySpawn = 0;
    let nextItemSpawn = 0;

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
        color: '#3333ff'
    };

    // オブジェクト配列
    let enemies = [];
    let items = [];

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
                player.dy = -12;
            }
        }
        if (e.code === 'KeyR' && gameOver) resetGame();
    });

    document.addEventListener('keyup', (e) => {
        if (e.code === 'KeyD') keys.right = false;
        if (e.code === 'KeyA') keys.left = false;
    });

    // 乱数生成ヘルパー
    function randomRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    function spawnEnemy() {
        const type = Math.random() < 0.5 ? 'ground' : 'flying';
        
        let enemy = {
            x: canvas.width,
            y: 0,
            width: 30,
            height: 30,
            dx: -randomRange(2, 4), // 速度をランダムに
            dy: 0,
            type: type,
            angle: 0, // 上下移動用
            color: '#ff3333'
        };

        if (type === 'ground') {
            enemy.y = GROUND_Y - enemy.height;
        } else {
            // 空中の敵（高さはランダム、かつ少し高め）
            enemy.y = randomRange(200, 280);
            enemy.color = '#cc0000'; // 空の敵は少し暗い赤
        }

        enemies.push(enemy);

        // 次の敵が出るまでの時間をランダム設定 (60フレーム = 1秒)
        nextEnemySpawn = frameCount + randomRange(60, 150);
    }

    function spawnItem() {
        items.push({
            x: canvas.width,
            y: randomRange(150, 320), // ジャンプして届く範囲にランダム配置
            width: 20,
            height: 20,
            dx: -2, // 地面と同じ速度で流れる
            color: '#FFD700' // 金色
        });
        
        // 次のアイテムが出るまでの時間
        nextItemSpawn = frameCount + randomRange(40, 100);
    }

    function resetGame() {
        player.x = 100;
        player.y = 300;
        player.dx = 0;
        player.dy = 0;
        score = 0;
        enemies = [];
        items = [];
        gameOver = false;
        frameCount = 0;
        nextEnemySpawn = 50;
        nextItemSpawn = 30;
        scoreEl.innerText = score;
        msgEl.style.display = 'none';
        loop();
    }

    function update() {
        if (gameOver) return;
        frameCount++;

        // --- プレイヤー処理 ---
        if (keys.right) player.dx = player.speed;
        else if (keys.left) player.dx = -player.speed;
        else player.dx *= FRICTION;

        player.x += player.dx;
        player.y += player.dy;
        player.dy += GRAVITY;

        // 地面判定
        if (player.y + player.height > GROUND_Y) {
            player.y = GROUND_Y - player.height;
            player.dy = 0;
            player.jumping = false;
        }

        // 画面端制限
        if (player.x < 0) player.x = 0;
        if (player.x + player.width > canvas.width) player.x = canvas.width - player.width;

        // --- 生成処理 ---
        if (frameCount >= nextEnemySpawn) spawnEnemy();
        if (frameCount >= nextItemSpawn) spawnItem();

        // --- アイテム処理 ---
        for (let i = 0; i < items.length; i++) {
            let item = items[i];
            item.x += item.dx;

            // 画面外削除
            if (item.x + item.width < 0) {
                items.splice(i, 1);
                i--;
                continue;
            }

            // 当たり判定（取得）
            if (
                player.x < item.x + item.width &&
                player.x + player.width > item.x &&
                player.y < item.y + item.height &&
                player.y + player.height > item.y
            ) {
                score += 50; // スコア加算
                scoreEl.innerText = score;
                items.splice(i, 1);
                i--;
            }
        }

        // --- 敵処理 ---
        for (let i = 0; i < enemies.length; i++) {
            let e = enemies[i];
            e.x += e.dx;

            // 空飛ぶ敵の波打ち移動
            if (e.type === 'flying') {
                e.angle += 0.1;
                e.y += Math.sin(e.angle) * 2; // ふわふわ動く
            }

            // 画面外削除
            if (e.x + e.width < 0) {
                enemies.splice(i, 1);
                i--;
                continue;
            }

            // 当たり判定
            if (
                player.x < e.x + e.width &&
                player.x + player.width > e.x &&
                player.y < e.y + e.height &&
                player.y + player.height > e.y
            ) {
                // 上から踏んだか？
                // (プレイヤーが落下中 かつ 敵の少し上にいる)
                if (player.dy > 0 && player.y + player.height < e.y + e.height * 0.6) {
                    enemies.splice(i, 1);
                    i--;
                    player.dy = -10; // 踏んでジャンプ
                    score += 100;
                    scoreEl.innerText = score;
                } else {
                    // ぶつかった
                    gameOver = true;
                    msgEl.style.display = 'block';
                }
            }
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 地面
        ctx.fillStyle = '#654321';
        ctx.fillRect(0, GROUND_Y, canvas.width, 40);
        ctx.fillStyle = '#32CD32';
        ctx.fillRect(0, GROUND_Y, canvas.width, 10);

        // アイテム（黄色い丸）
        ctx.fillStyle = '#FFD700';
        for (let item of items) {
            ctx.beginPath();
            ctx.arc(item.x + item.width/2, item.y + item.height/2, item.width/2, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = 'orange';
            ctx.stroke();
        }

        // 敵
        for (let e of enemies) {
            ctx.fillStyle = e.color;
            ctx.fillRect(e.x, e.y, e.width, e.height);
            // 敵の目（進行方向）
            ctx.fillStyle = 'white';
            ctx.fillRect(e.x + 5, e.y + 5, 10, 10);
        }

        // プレイヤー
        ctx.fillStyle = player.color;
        ctx.fillRect(player.x, player.y, player.width, player.height);
        // プレイヤーの目
        ctx.fillStyle = 'white';
        if (keys.left) ctx.fillRect(player.x + 5, player.y + 5, 10, 10); // 左向きの目
        else ctx.fillRect(player.x + 15, player.y + 5, 10, 10); // 右向きの目
    }

    function loop() {
        update();
        draw();
        if (!gameOver) requestAnimationFrame(loop);
    }

    // 初期化してスタート
    resetGame();

</script>
</body>
</html>
"""

components.html(game_html, height=500)
