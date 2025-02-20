import streamlit as st
import sqlite3
import io
from PIL import Image

# SQLite データベース接続
conn = sqlite3.connect('shop_db.db', check_same_thread=False)
c = conn.cursor()

# メニューのテーブル作成（画像データ BLOB を含む）
c.execute('''
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    price INTEGER NOT NULL,
    image BLOB
)
''')

# 売上テーブル作成
c.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    price INTEGER NOT NULL
)
''')
conn.commit()

# 生徒用画面 or おばちゃん用画面の切り替え
st.sidebar.title("画面の切り替え")
mode = st.sidebar.radio("選択してください", ["生徒用画面", "おばちゃん用画面"])

# 生徒用画面
if mode == "生徒用画面":
    st.title("📌 購買部メニュー")
    
    # メニューを表示
    c.execute("SELECT id, item, price, image FROM menu")
    menu_items = c.fetchall()

    cart = []
    total_price = 0

    for item_id, item_name, price, image_data in menu_items:
        cols = st.columns([2, 1, 1])  # レイアウト調整

        # 商品名と価格を表示
        cols[0].write(f"**{item_name}**")
        cols[1].write(f"{price} 円")

        # 画像を表示（存在する場合）
        if image_data:
            image = Image.open(io.BytesIO(image_data))
            cols[0].image(image, width=100)

        # 商品をカートに追加
        if cols[2].button(f"追加", key=f"add_{item_id}"):
            cart.append((item_name, price))
            total_price += price

    # カートの内容を表示
    st.subheader("🛒 選択した商品")
    if cart:
        for item_name, price in cart:
            st.write(f"- {item_name} ({price} 円)")

        st.write(f"**合計金額: {total_price} 円**")
        if st.button("会計する"):
            for item_name, price in cart:
                c.execute("INSERT INTO sales (item, price) VALUES (?, ?)", (item_name, price))
            conn.commit()
            st.success("購入が完了しました！")
    else:
        st.write("商品を選択してください。")

# おばちゃん用画面（パスコード認証あり）
else:
    st.title("🔒 おばちゃん用管理画面")

    # パスコード入力
    password = st.text_input("パスコードを入力", type="password")

    if password == "1234":  # シンプルなパスコード（必要なら変更）
        st.success("✅ 認証成功")

        # **メニュー追加**
        st.subheader("📌 新しい商品を登録")
        new_item = st.text_input("商品名")
        new_price = st.number_input("価格", min_value=0)

        uploaded_file = st.file_uploader("商品画像をアップロード", type=["jpg", "png", "jpeg"])
        captured_image = st.camera_input("カメラで撮影")

        # 画像データ処理
        image_data = None
        if uploaded_file:
            image = Image.open(uploaded_file)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            image_data = img_byte_arr.getvalue()
        elif captured_image:
            image = Image.open(captured_image)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            image_data = img_byte_arr.getvalue()

        if st.button("商品を登録"):
            if new_item and new_price > 0:
                c.execute("INSERT INTO menu (item, price, image) VALUES (?, ?, ?)", 
                          (new_item, new_price, sqlite3.Binary(image_data) if image_data else None))
                conn.commit()
                st.success(f"{new_item} が登録されました！")
            else:
                st.error("商品名と価格を入力してください。")

        # **メニュー一覧（削除機能付き）**
        st.subheader("🗑️ 商品管理")
        c.execute("SELECT id, item, price FROM menu")
        menu_items = c.fetchall()

        for item_id, item_name, price in menu_items:
            cols = st.columns([2, 1, 1])

            cols[0].write(f"**{item_name}**")
            cols[1].write(f"{price} 円")

            if cols[2].button("削除", key=f"del_{item_id}"):
                c.execute("DELETE FROM menu WHERE id=?", (item_id,))
                conn.commit()
                st.warning(f"{item_name} を削除しました。")
                st.experimental_rerun()  # ページをリロード

        # **売上履歴**
        st.subheader("📈 売上履歴")
        c.execute("SELECT item, price FROM sales")
        sales_data = c.fetchall()

        if sales_data:
            for item_name, price in sales_data:
                st.write(f"- {item_name} ({price} 円)")
        else:
            st.write("売上データがありません。")

    else:
        st.error("パスコードが間違っています。")
