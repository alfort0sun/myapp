import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

# モバイル対応のためのページ設定
st.set_page_config(
    page_title="家計簿アプリ",
    layout="wide",  # デスクトップではワイドレイアウト
    initial_sidebar_state="collapsed"  # モバイルではサイドバー非表示
)

# モバイル向けCSSスタイル
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        height: 50px;
        font-size: 16px;
    }
    .stSelectbox div div div {
        height: 50px;
    }
    .stNumberInput div div div input {
        height: 50px;
        font-size: 16px;
    }
    .stTextInput div div div input {
        height: 50px;
        font-size: 16px;
    }
    .stDateInput div div div div {
        height: 50px;
    }
    .stRadio div div label {
        font-size: 16px;
    }
    .stTabs button {
        height: 60px;
        font-size: 18px;
    }
    /* グラフの高さを調整 */
    .js-plotly-plot {
        height: 300px !important;
    }
    /* メトリック値を大きく表示 */
    .css-1wivap2 {
        font-size: 24px !important;
    }
</style>
""", unsafe_allow_html=True)

# アプリのタイトル
st.title("シンプル家計簿")

# データファイルのパス
DATA_FILE = "household_data.json"

# 初期データの読み込み
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"transactions": []}

# データの保存
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# 初期データの読み込み
data = load_data()

# トランザクションをDataFrameに変換
def get_transactions_df():
    if data["transactions"]:
        return pd.DataFrame(data["transactions"])
    else:
        return pd.DataFrame(columns=["日付", "カテゴリ", "タイプ", "金額", "メモ"])

# タブでメニューを作成（タブのサイズを大きくしてタップしやすく）
tab1, tab2, tab3 = st.tabs(["💰 入力", "📋 履歴", "📊 分析"])

# 入力タブ
with tab1:
    st.header("収支の入力")
    
    # フォームを作成
    with st.form("transaction_form"):
        # 日付入力
        date = st.date_input(
            "日付",
            value=datetime.now()
        )
        
        # 収支のタイプ - 横並びで大きく表示
        st.write("収支タイプ")
        transaction_type = st.radio(
            "",
            options=["支出", "収入"],
            horizontal=True
        )
        
        # カテゴリ選択
        if transaction_type == "支出":
            categories = ["食費", "住居費", "光熱費", "通信費", "交通費", "衣類", "医療", "教育", "娯楽", "その他"]
        else:
            categories = ["給料", "ボーナス", "副収入", "その他"]
        
        category = st.selectbox("カテゴリ", categories)
        
        # 金額入力 - 数字キーボードが表示されるように
        st.write("金額（円）")
        amount = st.number_input("", min_value=0, value=0, step=100)
        
        # メモ入力
        memo = st.text_input("メモ（任意）")
        
        # 送信ボタン - 大きく
        submitted = st.form_submit_button("保存")
        
        if submitted and amount > 0:
            # トランザクションの追加
            new_transaction = {
                "日付": date.strftime("%Y-%m-%d"),
                "カテゴリ": category,
                "タイプ": transaction_type,
                "金額": amount,
                "メモ": memo
            }
            
            data["transactions"].append(new_transaction)
            save_data(data)
            st.success("保存しました！")

# 履歴タブ
with tab2:
    st.header("収支の履歴")
    
    # フィルター（モバイル向けに縦に配置）
    st.subheader("フィルター")
    
    filter_type = st.multiselect(
        "収支タイプ",
        options=["支出", "収入"],
        default=["支出", "収入"]
    )
    
    # 全てのカテゴリを取得
    df = get_transactions_df()
    if not df.empty and "カテゴリ" in df.columns:
        all_categories = df["カテゴリ"].unique().tolist()
    else:
        all_categories = []
    
    filter_category = st.multiselect(
        "カテゴリ",
        options=all_categories,
        default=all_categories
    )
    
    # データの表示
    df = get_transactions_df()
    
    if not df.empty:
        # フィルター適用
        if filter_type:
            df = df[df["タイプ"].isin(filter_type)]
        
        if filter_category:
            df = df[df["カテゴリ"].isin(filter_category)]
        
        # 日付でソート
        if "日付" in df.columns:
            df["日付"] = pd.to_datetime(df["日付"])
            df = df.sort_values("日付", ascending=False)
        
        # 合計金額の表示 - モバイルでは縦に並べる
        income_total = df[df["タイプ"] == "収入"]["金額"].sum()
        expense_total = df[df["タイプ"] == "支出"]["金額"].sum()
        balance = income_total - expense_total
        
        st.metric("収入合計", f"{income_total:,}円")
        st.metric("支出合計", f"{expense_total:,}円")
        st.metric("収支差額", f"{balance:,}円", delta=f"{balance:,}円")
        
        # スクロール可能なデータフレーム表示
        st.write("取引履歴")
        
        # モバイル用に表示するカラムを制限
        mobile_df = df[["日付", "タイプ", "カテゴリ", "金額"]].copy()
        mobile_df["金額"] = mobile_df["金額"].apply(lambda x: f"{x:,}円")
        
        st.dataframe(
            mobile_df,
            use_container_width=True,
            height=300
        )
        
        # 詳細表示を折りたたみメニューに
        with st.expander("すべての詳細を表示"):
            st.dataframe(
                df,
                use_container_width=True
            )
    else:
        st.info("データがありません。「入力」タブから収支を追加してください。")

# 分析タブ
with tab3:
    st.header("収支の分析")
    
    df = get_transactions_df()
    
    if not df.empty and len(df) > 0:
        # 日付を変換
        if "日付" in df.columns:
            df["日付"] = pd.to_datetime(df["日付"])
        
        # 期間選択 - モバイル向けに上下に配置
        period = st.selectbox(
            "期間",
            options=["過去7日間", "過去30日間", "過去3ヶ月", "過去6ヶ月", "過去1年", "全期間"]
        )
        
        # 期間でフィルタリング
        today = datetime.now().date()
        
        if period == "過去7日間":
            start_date = today - timedelta(days=7)
        elif period == "過去30日間":
            start_date = today - timedelta(days=30)
        elif period == "過去3ヶ月":
            start_date = today - timedelta(days=90)
        elif period == "過去6ヶ月":
            start_date = today - timedelta(days=180)
        elif period == "過去1年":
            start_date = today - timedelta(days=365)
        else:  # 全期間
            start_date = df["日付"].min().date()
        
        filtered_df = df[df["日付"].dt.date >= start_date]
        
        if len(filtered_df) > 0:
            # 月別の収支推移 - モバイルでも見やすいようにシンプルに
            st.subheader("月別収支")
            
            # 月ごとの集計
            filtered_df["年月"] = filtered_df["日付"].dt.strftime("%Y-%m")
            monthly_expense = filtered_df[filtered_df["タイプ"] == "支出"].groupby("年月")["金額"].sum().reset_index()
            monthly_income = filtered_df[filtered_df["タイプ"] == "収入"].groupby("年月")["金額"].sum().reset_index()
            
            # マージして月別収支を作成
            monthly_data = pd.merge(monthly_income, monthly_expense, on="年月", how="outer", suffixes=("_収入", "_支出"))
            monthly_data = monthly_data.fillna(0)
            monthly_data["収支"] = monthly_data["金額_収入"] - monthly_data["金額_支出"]
            
            # グラフ表示 - シンプルでモバイルフレンドリーなグラフ
            fig = px.bar(
                monthly_data,
                x="年月",
                y=["金額_収入", "金額_支出"],
                title="月別収支",
                labels={"value": "金額", "variable": "タイプ"},
                barmode="group",
                height=350  # モバイル向けに高さ調整
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # カテゴリ別の集計
            st.subheader("カテゴリ別集計")
            
            # 表示タイプを選択できるように
            analysis_type = st.radio(
                "表示する内訳",
                options=["支出", "収入"],
                horizontal=True
            )
            
            if analysis_type == "支出":
                expense_df = filtered_df[filtered_df["タイプ"] == "支出"]
                if len(expense_df) > 0:
                    expense_by_category = expense_df.groupby("カテゴリ")["金額"].sum().reset_index()
                    fig = px.pie(
                        expense_by_category,
                        values="金額",
                        names="カテゴリ",
                        title="支出内訳",
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # カテゴリ別の金額表示（モバイル向け）
                    expense_by_category = expense_by_category.sort_values("金額", ascending=False)
                    expense_by_category["金額"] = expense_by_category["金額"].apply(lambda x: f"{x:,}円")
                    st.dataframe(expense_by_category, use_container_width=True)
                else:
                    st.info("この期間の支出データがありません")
            else:
                income_df = filtered_df[filtered_df["タイプ"] == "収入"]
                if len(income_df) > 0:
                    income_by_category = income_df.groupby("カテゴリ")["金額"].sum().reset_index()
                    fig = px.pie(
                        income_by_category,
                        values="金額",
                        names="カテゴリ",
                        title="収入内訳",
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # カテゴリ別の金額表示（モバイル向け）
                    income_by_category = income_by_category.sort_values("金額", ascending=False)
                    income_by_category["金額"] = income_by_category["金額"].apply(lambda x: f"{x:,}円")
                    st.dataframe(income_by_category, use_container_width=True)
                else:
                    st.info("この期間の収入データがありません")
        else:
            st.info(f"選択した期間（{start_date} から {today}）のデータがありません。")
    else:
        st.info("データがありません。「入力」タブから収支を追加してください。")

# 設定エリア（サイドバーに表示 - モバイルではハンバーガーメニューから）
with st.sidebar:
    st.header("設定")
    
    # サンプルデータの追加
    if st.button("サンプルデータを追加", key="add_sample"):
        sample_data = [
            {"日付": "2023-03-01", "カテゴリ": "給料", "タイプ": "収入", "金額": 280000, "メモ": "3月分給料"},
            {"日付": "2023-03-05", "カテゴリ": "食費", "タイプ": "支出", "金額": 5000, "メモ": "スーパーでの買い物"},
            {"日付": "2023-03-10", "カテゴリ": "住居費", "タイプ": "支出", "金額": 80000, "メモ": "家賃"},
            {"日付": "2023-03-15", "カテゴリ": "通信費", "タイプ": "支出", "金額": 8000, "メモ": "携帯料金"},
            {"日付": "2023-03-20", "カテゴリ": "光熱費", "タイプ": "支出", "金額": 12000, "メモ": "電気・ガス・水道"},
            {"日付": "2023-03-25", "カテゴリ": "娯楽", "タイプ": "支出", "金額": 15000, "メモ": "映画と食事"},
            {"日付": "2023-04-01", "カテゴリ": "給料", "タイプ": "収入", "金額": 280000, "メモ": "4月分給料"},
            {"日付": "2023-04-05", "カテゴリ": "食費", "タイプ": "支出", "金額": 6000, "メモ": "スーパーでの買い物"},
            {"日付": "2023-04-10", "カテゴリ": "住居費", "タイプ": "支出", "金額": 80000, "メモ": "家賃"},
            {"日付": "2023-04-12", "カテゴリ": "衣類", "タイプ": "支出", "金額": 20000, "メモ": "春物衣類"},
            {"日付": "2023-04-15", "カテゴリ": "通信費", "タイプ": "支出", "金額": 8000, "メモ": "携帯料金"},
            {"日付": "2023-04-20", "カテゴリ": "光熱費", "タイプ": "支出", "金額": 10000, "メモ": "電気・ガス・水道"},
            {"日付": "2023-04-28", "カテゴリ": "副収入", "タイプ": "収入", "金額": 30000, "メモ": "副業収入"},
        ]
        
        for transaction in sample_data:
            if transaction not in data["transactions"]:
                data["transactions"].append(transaction)
        
        save_data(data)
        st.success("サンプルデータを追加しました")
        st.experimental_rerun()
    
    # データのリセット
    if st.button("全データを削除", key="delete_data"):
        st.warning("⚠️ この操作は元に戻せません")
        confirm = st.checkbox("本当に全てのデータを削除しますか？")
        if confirm:
            data = {"transactions": []}
            save_data(data)
            st.success("全てのデータを削除しました")
            st.experimental_rerun()
    
    # データのエクスポート機能
    if len(data["transactions"]) > 0:
        st.write("---")
        st.subheader("データエクスポート")
        
        # CSVダウンロード機能
        df = get_transactions_df()
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="CSVダウンロード",
            data=csv,
            file_name="household_data.csv",
            mime="text/csv",
        )
    
    # アプリ情報
    st.markdown("---")
    st.caption("シンプル家計簿アプリ v1.1")
    st.caption("Streamlitで作成")