import streamlit as st
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(page_title="Action Game with Ranking & Animation", layout="wide")

# ==========================================
# 👇 ここに GAS (Google Apps Script) のウェブアプリURLを貼ってください
# ==========================================
GAS_API_URL = "https://script.google.com/macros/s/AKfycbxMxXwluhonVbnunqMc11rJv5rCQhUDcmm6ZTKLyMxyBeVtjKkSCCeI6FHj4V4An8MLgw/exec"


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

st.caption("機能：❤️ライフ / 🆙レベル / ☁️背景変化 / 🔊音 / 🏆ランク / 🏃‍♂️アニメ / 🎵BGM / ✨アイテム / 🧗‍♂️段差 / 💥コンボ / 🫨シェイク / 📏サイズ / 🦘2段ジャンプ / ✨撃破演出 / ⬇️しゃがみ / ⏩横スクロール / 🧱空中足場 / ⛩️ゲート / 🗻パララックス / 🕹️スティック操作 / 📱縦画面最適化")
st.write("操作方法: **W** ジャンプ(2回可) / **A** 左移動 / **D** 右移動 / **S** しゃがみ / **R** リセット / **F** 全画面")

# HTMLファイルを読み込む
try:
    with open("game.html", "r", encoding="utf-8") as f:
        game_html_content = f.read()

    # GASのURLを埋め込む（HTML内の {GAS_API_URL} を置換）
    game_html_content = game_html_content.replace("{GAS_API_URL}", GAS_API_URL)

    # ゲームを表示
    components.html(game_html_content, height=550, scrolling=False)

except FileNotFoundError:
    st.error("エラー: 'game.html' が見つかりません。同じフォルダに保存してください。")
