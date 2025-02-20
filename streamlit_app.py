import streamlit as st
import sqlite3

# ページ設定
st.set_page_config(page_title="購買部効率化アプリ", layout="wide")

# パスコードの設定
ADMIN_PASSWORD = "koubai123"  # おばちゃん用画面のパスコード

# データベース接続
conn = sqlite3.connect('shop_db.db')
c = conn.cursor()

# メニュー作成（サンプル）
menu = {
    "パン": 150,
    "ジュース": 200,
    "おにぎり": 120,
    "お菓子": 100
}

# タイトル
st.title("購買部効率化アプリ")

# 生徒用画面とおばちゃん用画面を切り替える
mode = st.radio("モードを選択してください", ("生徒用", "おばちゃん用"))

# 生徒用画面
if mode == "生徒用":
    st.header("メニュー")
    
    # メニュー選択
    items_selected = {}
    for item, price in menu.items():
        items_selected[item] = st.checkbox(f"{item} ({price}円)")

    total = 0
    for item, selected in items_selected.items():
        if selected:
            total += menu[item]

    if total > 0:
        st.write(f"合計金額: {total}円")
        if st.button("支払う"):
            st.success(f"支払いが完了しました！ {total}円")
    else:
        st.info("商品を選択してください")

# おばちゃん用画面
elif mode == "おばちゃん用":
    password = st.text_input("パスコードを入力してください", type="password")
    
    # パスコードチェック
    if password == ADMIN_PASSWORD:
        st.header("売れた商品")
        
        # 売れた商品を表示（データベースから取得）
        c.execute("SELECT * FROM sales")
        sales = c.fetchall()

        if sales:
            st.write("売上履歴:")
            for sale in sales:
                st.write(f"商品: {sale[1]}, 数量: {sale[2]}, 合計: {sale[3]}円")
        else:
            st.write("現在、売上はありません。")

        # メニュー登録機能
        st.header("新商品を登録")
        new_item = st.text_input("商品名")
        new_price = st.number_input("価格", min_value=0)

        if st.button("商品を登録"):
            if new_item and new_price > 0:
                c.execute("INSERT INTO menu (item, price) VALUES (?, ?)", (new_item, new_price))
                conn.commit()
                st.success(f"{new_item}が登録されました！")
            else:
                st.error("商品名と価格を正しく入力してください。")

    else:
        st.error("パスコードが間違っています。")
