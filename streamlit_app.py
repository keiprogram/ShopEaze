import streamlit as st
import sqlite3
import io
from PIL import Image

# ページ設定
st.set_page_config(page_title="購買部効率化アプリ", layout="wide")

# パスコード設定
ADMIN_PASSWORD = "admin123"

# SQLiteデータベースの初期化
conn = sqlite3.connect('shop_db.db', check_same_thread=False)
c = conn.cursor()

# テーブル作成（画像データをBLOBとして格納）
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
    quantity INTEGER NOT NULL,
    total INTEGER NOT NULL
)
''')

conn.commit()

# タイトル
st.title("購買部効率化アプリ")

# 生徒用画面とおばちゃん用画面の切り替え
mode = st.radio("モードを選択してください", ("生徒用", "おばちゃん用"))

# 生徒用画面
if mode == "生徒用":
    st.header("メニュー")

    # メニューをデータベースから取得
    c.execute("SELECT * FROM menu")
    menu_items = c.fetchall()

    items_selected = {}
    total = 0

    for item in menu_items:
        item_id, item_name, price, image_data = item

        col1, col2 = st.columns([1, 3])
        with col1:
            if image_data:
                image = Image.open(io.BytesIO(image_data))
                st.image(image, width=100)

        with col2:
            selected = st.checkbox(f"{item_name} ({price}円)")
            items_selected[item_name] = selected
            if selected:
                total += price

    # 合計金額表示
    if total > 0:
        st.write(f"**合計金額: {total}円**")
        if st.button("支払う"):
            st.success(f"支払いが完了しました！ {total}円")
            for item_name, selected in items_selected.items():
                if selected:
                    c.execute("INSERT INTO sales (item, quantity, total) VALUES (?, ?, ?)", (item_name, 1, price))
            conn.commit()
    else:
        st.info("商品を選択してください")

# おばちゃん用画面
elif mode == "おばちゃん用":
    password = st.text_input("パスコードを入力してください", type="password")

    if password == ADMIN_PASSWORD:
        st.header("売れた商品")

        # 売上履歴を表示
        c.execute("SELECT * FROM sales")
        sales = c.fetchall()

        if sales:
            for sale in sales:
                st.write(f"**商品:** {sale[1]}  |  **数量:** {sale[2]}  |  **合計:** {sale[3]}円")
        else:
            st.write("現在、売上はありません。")

        # メニュー登録機能
        st.header("新商品を登録")
        new_item = st.text_input("商品名")
        new_price = st.number_input("価格", min_value=0)

        # 画像アップロードまたはカメラ撮影
        uploaded_file = st.file_uploader("商品画像をアップロード", type=["jpg", "png", "jpeg"])
        captured_image = st.camera_input("カメラで撮影")

        # 画像の処理
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

        # 商品を登録
        if st.button("商品を登録"):
            if new_item and new_price > 0:
                # データベースに登録（画像データは BLOB 形式で保存）
                c.execute("INSERT INTO menu (item, price, image) VALUES (?, ?, ?)", 
                          (new_item, new_price, sqlite3.Binary(image_data) if image_data else None))
                conn.commit()
                st.success(f"{new_item}が登録されました！")
            else:
                st.error("商品名と価格を正しく入力してください。")

        # メニュー削除機能
        st.header("メニューを削除")

        # 現在のメニューリストを取得
        c.execute("SELECT * FROM menu")
        menu_items = c.fetchall()

        if menu_items:
            menu_to_delete = st.selectbox("削除する商品を選んでください", [item[1] for item in menu_items])

            if st.button("選択した商品を削除"):
                selected_item = next(item for item in menu_items if item[1] == menu_to_delete)
                item_id = selected_item[0]

                c.execute("DELETE FROM menu WHERE id = ?", (item_id,))
                conn.commit()

                st.success(f"商品「{menu_to_delete}」が削除されました。")
        else:
            st.write("現在、削除できるメニューはありません。")
    else:
        st.error("パスコードが間違っています。")
