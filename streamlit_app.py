import streamlit as st
import sqlite3

# ページ設定
st.set_page_config(page_title="購買部効率化アプリ", layout="wide")

# パスコードの設定
ADMIN_PASSWORD = "admin123"  # おばちゃん用画面のパスコード

# SQLiteデータベースの初期化
conn = sqlite3.connect('shop_db.db')
c = conn.cursor()

# テーブル作成（もしテーブルが存在しなければ作成する）
c.execute('''
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    price INTEGER NOT NULL
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

# 生徒用画面とおばちゃん用画面を切り替える
mode = st.radio("モードを選択してください", ("生徒用", "おばちゃん用"))

# 生徒用画面
if mode == "生徒用":
    st.header("メニュー")

    # メニューをデータベースから動的に読み込む
    c.execute("SELECT * FROM menu")
    menu = {item[1]: item[2] for item in c.fetchall()}

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
            # 支払いが完了したら売上データをsalesテーブルに記録
            for item, selected in items_selected.items():
                if selected:
                    c.execute("INSERT INTO sales (item, quantity, total) VALUES (?, ?, ?)", 
                              (item, 1, menu[item]))
            conn.commit()
    else:
        st.info("商品を選択してください")

# おばちゃん用画面
elif mode == "おばちゃん用":
    password = st.text_input("パスコードを入力してください", type="password")
    
    # パスコードチェック
    if password == ADMIN_PASSWORD:
        st.header("売れた商品")
        
        # 売れた商品を表示（データベースから取得）
        try:
            c.execute("SELECT * FROM sales")
            sales = c.fetchall()

            if sales:
                st.write("売上履歴:")
                for sale in sales:
                    st.write(f"商品: {sale[1]}, 数量: {sale[2]}, 合計: {sale[3]}円")
            else:
                st.write("現在、売上はありません。")
        except sqlite3.OperationalError as e:
            st.error(f"エラーが発生しました: {str(e)}")

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

        # メニュー削除機能
        st.header("メニューを削除")
        
        # メニューリストを取得
        c.execute("SELECT * FROM menu")
        menu_items = c.fetchall()

        if menu_items:
            # メニュー削除用に選択肢を表示
            menu_to_delete = st.selectbox("削除する商品を選んでください", [item[1] for item in menu_items])

            if st.button("選択した商品を削除"):
                # 選ばれた商品のIDを取得
                selected_item = next(item for item in menu_items if item[1] == menu_to_delete)
                item_id = selected_item[0]

                # メニューから削除
                c.execute("DELETE FROM menu WHERE id = ?", (item_id,))
                conn.commit()

                st.success(f"商品「{menu_to_delete}」が削除されました。")
        else:
            st.write("現在、削除できるメニューはありません。")

    else:
        st.error("パスコードが間違っています。")
