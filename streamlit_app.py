import streamlit as st
import sqlite3
import io
from PIL import Image

# データベース接続
conn = sqlite3.connect('shop_db.db', check_same_thread=False)
c = conn.cursor()

# **テーブルの作成と更新**
def initialize_database():
    # `menu` テーブルに `stock` カラムがあるかチェック
    c.execute("PRAGMA table_info(menu)")
    columns = [col[1] for col in c.fetchall()]

    if "stock" not in columns:
        c.execute("ALTER TABLE menu ADD COLUMN stock INTEGER DEFAULT 0")

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

# **画面の切り替え**
st.sidebar.title("画面の切り替え")
mode = st.sidebar.radio("選択してください", ["生徒用画面", "おばちゃん用画面"])

# **生徒用画面**
if mode == "生徒用画面":
    st.image("img/rogo2.png")
    st.title("📌 購買部メニュー")

    # メニューを取得
    try:
        c.execute("SELECT id, item, price, stock, image FROM menu")
        menu_items = c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"データベースエラー: {e}")
        st.stop()

    # 選択した商品のリスト
    if 'cart' not in st.session_state:
        st.session_state.cart = []

    cols = st.columns(2)

    for index, (item_id, item_name, price, stock, image_data) in enumerate(menu_items):
        with cols[index % 2]:
            st.write(f"**{item_name}**")
            if image_data:
                image = Image.open(io.BytesIO(image_data))
                st.image(image, width=150)
            st.write(f"💰 {price} 円")
            st.write(f"📦 在庫: {stock} 個")

            if stock > 0:
                if st.button(f"追加", key=f"add_{item_id}"):
                    st.session_state.cart.append((item_id, item_name, price))
            else:
                st.write("🚫 売り切れ")

# カートが存在しない場合は初期化
if 'cart' not in st.session_state or not isinstance(st.session_state.cart, list):
    st.session_state.cart = []

# 🛒 選択した商品一覧
st.subheader("🛒 選択した商品")

if st.session_state.cart:
    total_price = 0
    items_to_remove = []

    for idx, (item_name, price) in enumerate(st.session_state.cart):
        col1, col2 = st.columns([3, 1])
        col1.write(f"- {item_name} ({price} 円)")
        
        # 🔴 取り消しボタン（該当アイテムをカートから削除）
        if col2.button(f"取り消し {idx}", key=f"remove_{idx}"):
            items_to_remove.append(idx)

    # 削除リストにある商品をカートから削除
    for idx in sorted(items_to_remove, reverse=True):
        del st.session_state.cart[idx]

    # 合計金額の計算と表示
    total_price = sum(price for _, price in st.session_state.cart)
    st.markdown(f"## 💰 合計金額: {total_price} 円")

    # ✅ 購入ボタン
    if st.button("購入する"):
        for item_name, price in st.session_state.cart:
            c.execute("INSERT INTO sales (item, price) VALUES (?, ?)", (item_name, price))
        conn.commit()
        st.success("購入が完了しました！")
        st.session_state.cart = []
        st.rerun()
    else:
        st.write("🛍️ 商品を選択してください。")


# **おばちゃん用画面**
else:
    st.title("🔒 おばちゃん用管理画面")
    st.image("img/rogo2.png")
    password = st.text_input("パスコードを入力", type="password")

    if password == "koubaibu":
        st.success("✅ 認証成功")

        # **メニュー追加**
        st.subheader("📌 新しい商品を登録")
        new_item = st.text_input("商品名")
        new_price = st.number_input("価格", min_value=0)
        new_stock = st.number_input("在庫数", min_value=0, step=1)
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
            if new_item and new_price > 0 and new_stock >= 0:
                c.execute("INSERT INTO menu (item, price, stock, image) VALUES (?, ?, ?, ?)", 
                          (new_item, new_price, new_stock, sqlite3.Binary(image_data) if image_data else None))
                conn.commit()
                st.success(f"{new_item} が登録されました！")
                st.rerun()
            else:
                st.error("商品名・価格・在庫を入力してください。")

        # **メニュー一覧**
        st.subheader("🗑️ 商品管理")
        c.execute("SELECT id, item, price, stock FROM menu")
        menu_items = c.fetchall()

        for item_id, item_name, price, stock in menu_items:
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"**{item_name}**")
            cols[1].write(f"{price} 円")
            cols[2].write(f"在庫: {stock} 個")

            if cols[3].button("削除", key=f"del_{item_id}"):
                c.execute("DELETE FROM menu WHERE id=?", (item_id,))
                conn.commit()
                st.warning(f"{item_name} を削除しました。")
                st.rerun()

               # **売上**
        st.subheader("📊 売上")

        # 売上データを取得
        c.execute("SELECT item, price, timestamp FROM sales ORDER BY timestamp DESC")
        sales_data = c.fetchall()

        if sales_data:
            # 売上データをPandasのDataFrameに変換
            import pandas as pd
            df = pd.DataFrame(sales_data, columns=["商品名", "価格", "購入日時"])
            df["購入日時"] = pd.to_datetime(df["購入日時"])
            df["日付"] = df["購入日時"].dt.date  # 日付ごとに集計するための列を作成

            # **売上の表を表示**
            st.dataframe(df[["日付", "商品名", "価格"]].sort_values(by="日付", ascending=False))

            # **日ごとの売上合計を計算**
            daily_sales = df.groupby("日付")["価格"].sum().reset_index()
            daily_sales.columns = ["日付", "売上合計"]

            # **日ごとの売上合計を表示**
            st.subheader("📅 日ごとの売上合計")
            st.dataframe(daily_sales.sort_values(by="日付", ascending=False))

        else:
            st.write("📉 売上データがありません。")

