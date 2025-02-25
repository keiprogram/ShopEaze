import streamlit as st
import sqlite3
import io
from PIL import Image

# データベース接続
conn = sqlite3.connect('shop_db.db', check_same_thread=False)
c = conn.cursor()

# テーブルを作成
def initialize_database():
    c.execute('''
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        price INTEGER NOT NULL,
        image BLOB
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        price INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()

initialize_database()

# 画面の切り替え
st.sidebar.title("画面の切り替え")
mode = st.sidebar.radio("選択してください", ["生徒用画面", "おばちゃん用画面"])

# **生徒用画面**
if mode == "生徒用画面":
    st.title("📌 購買部メニュー")
    
    # メニューを取得
    try:
        c.execute("SELECT id, item, price, image FROM menu")
        menu_items = c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"データベースエラー: {e}")
        st.stop()

    # 選択した商品のリスト
    if 'cart' not in st.session_state:
        st.session_state.cart = []

    for item_id, item_name, price, image_data in menu_items:
        cols = st.columns([2, 1, 1])
        cols[0].write(f"**{item_name}**")
        cols[1].write(f"{price} 円")

        if image_data:
            image = Image.open(io.BytesIO(image_data))
            cols[0].image(image, width=500)

        if cols[2].button(f"追加", key=f"add_{item_id}"):
            st.session_state.cart.append((item_name, price))

    # 購入リストの表示
    st.subheader("🛒 選択した商品")
    total_price = sum(price for _, price in st.session_state.cart)

    if st.session_state.cart:
        for item_name, price in st.session_state.cart:
            st.write(f"- {item_name} ({price} 円)")

        # 合計金額を大きく表示
        st.markdown(f"## 💰 合計金額: {total_price} 円")

        if st.button("購入する"):
            for item_name, price in st.session_state.cart:
                c.execute("INSERT INTO sales (item, price) VALUES (?, ?)", (item_name, price))
            conn.commit()
            st.success("購入が完了しました！")
            st.session_state.cart = []
            st.rerun()

    else:
        st.write("商品を選択してください。")

# **おばちゃん用画面**
else:
    st.title("🔒 おばちゃん用管理画面")
    password = st.text_input("パスコードを入力", type="password")

    if password == "koubaibu":
        st.success("✅ 認証成功")
        
        # **メニュー追加**
        st.subheader("📌 新しい商品を登録")
        new_item = st.text_input("商品名")
        new_price = st.number_input("価格", min_value=0)
        uploaded_file = st.file_uploader("商品画像をアップロード", type=["jpg", "png", "jpeg"])
        captured_image = st.camera_input("カメラで撮影")

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
                st.experimental_rerun()
            else:
                st.error("商品名と価格を入力してください。")

        # **メニュー一覧**
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
                st.experimental_rerun()

        # **売上履歴**
        st.subheader("📈 売上履歴")
        c.execute("SELECT item, price, timestamp FROM sales ORDER BY timestamp DESC")
        sales_data = c.fetchall()

        if sales_data:
            for item_name, price, timestamp in sales_data:
                st.write(f"- {timestamp} : **{item_name}** ({price} 円)")
        else:
            st.write("売上データがありません。")
    else:
        st.error("パスコードが間違っています。")
