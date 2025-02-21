import streamlit as st
import pandas as pd
import requests
import base64
import io
import urllib.parse
import unicodedata  # 追加
from baseballmetrics import *  # 追加


@st.cache_data(ttl=86400)
def load_csv_files_from_private_github():
    """
    st.secretsに設定したGitHub情報をもとに、指定フォルダ内の全CSVファイルを取得し、
    それぞれをDataFrameに読み込んだ上で、結合して返す関数。
    """
    # シークレットから必要な情報を取得
    token = st.secrets["github"]["token"]
    repo_owner = st.secrets["github"]["repo_owner"]
    repo_name = st.secrets["github"]["repo_name"]
    branch = st.secrets["github"].get("branch", "main")
    folder_path = st.secrets["github"]["folder_path"]

    # まずUnicode正規化（NFC）する
    folder_path_normalized = unicodedata.normalize('NFC', folder_path)
    # 正規化後のフォルダパスをURLエンコード（スラッシュは除外）
    folder_path_encoded = urllib.parse.quote(folder_path_normalized, safe="/")

    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder_path_encoded}?ref={branch}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        st.error(f"フォルダ内のファイル一覧が取得できませんでした。ステータスコード: {response.status_code}")
        return None

    files_info = response.json()
    csv_dfs = []
    for file in files_info:
        if file["type"] == "file" and file["name"].lower().endswith(".csv"):
            file_url = file["url"]
            file_response = requests.get(file_url, headers=headers)
            if file_response.status_code != 200:
                st.warning(f"{file['name']} の読み込みに失敗しました。ステータスコード: {file_response.status_code}")
                continue
            file_data = file_response.json()
            content_encoded = file_data["content"]
            content_decoded = base64.b64decode(content_encoded).decode("utf-8")
            df = pd.read_csv(io.StringIO(content_decoded))
            csv_dfs.append(df)
    if csv_dfs:
        combined_df = pd.concat(csv_dfs, ignore_index=True)
        return combined_df
    else:
        return None
    
def compute_batter_stats(df):
    """
    結合したdfを"Batter"ごとにグループ化し、各グループに対して
    指定された関数（seki, dasu, countpr, BA, OBP, SA, OPS）を適用して集計結果を返す。
    
    戻り値は各指標の列名を含むDataFrameで、列順は以下の通り:
    ['Batter', '打席', '打数', '安打', '二塁打', '三塁打', '本塁打', '四球', '三振', '打率', '出塁率', '長打率', 'OPS']
    """
    df = df.copy()
    df= df.query('BatterTeam == "TOK"').reset_index(drop=True)
    results = []
    # "Batter"という列でグループ化
    for batter, group in df.groupby("Batter"):
        # 各関数を適用（関数内部でgroupのデータを使って計算する前提）
        single = countpr(group, 'Single')
        double = countpr(group, 'Double')
        triple = countpr(group, 'Triple')
        homerun = countpr(group, 'HomeRun')
        stats = {
            "打者": batter,
            "打席": seki(group),
            "打数": dasu(group),
            "安打": single + double + triple + homerun,
            "単打": countpr(group, 'Single'),
            "二塁打": countpr(group, 'Double'),
            "三塁打": countpr(group, 'Triple'),
            "本塁打": countpr(group, 'HomeRun'),
            "四球": countpr(group, 'Walk'),
            "三振": countpr(group, 'Strikeout'),
            "打率": BA(group),
            "出塁率": OBP(group,mc=False),
            "長打率": SA(group),
            "OPS": OPS(group)
        }
        results.append(stats)
    
    # 結果をDataFrameに変換
    result_df = pd.DataFrame(results)
    # 表示順を整える
    result_df = result_df[["打者",  "打率", "出塁率", "長打率", "OPS","打席", "打数", "安打","単打", "二塁打", "三塁打", "本塁打", "四球", "三振",]].sort_values("OPS", ascending=False)
    return result_df

def main():
    st.title("オープン戦打者成績")
    st.write("現在の対象試合:2025春")
    
    df = load_csv_files_from_private_github()
    if df is None:
        st.error("CSVファイルが見つかりませんでした。")
        return

    try:
        st.sidebar.subheader("GameLevel")
        A_checked = st.sidebar.checkbox("A", value=True)
        B_checked = st.sidebar.checkbox("B", value=True)
    
        # フィルタリングのロジック
        if A_checked and not B_checked:
            df = df[df["Level"] == "A"]
        elif B_checked and not A_checked:
            df = df[df["Level"] == "B"]
        elif not A_checked and not B_checked:
            st.warning("少なくとも一方のGameLevel（A戦またはB戦）を選択してください。")
            return
        if len(df) == 0:
            st.warning("該当するデータがありません。")
            return
            # サイドバーにチェックボックスを設置して、PitcherThrowsでフィルタリングする
        st.sidebar.subheader("PitcherThrows")
        right_checked = st.sidebar.checkbox("Right", value=True)
        left_checked = st.sidebar.checkbox("Left", value=True)
    
        # フィルタリングのロジック
        if right_checked and not left_checked:
            df = df[df["PitcherThrows"] == "Right"]
        elif left_checked and not right_checked:
            df = df[df["PitcherThrows"] == "Left"]
        elif not right_checked and not left_checked:
            st.warning("少なくとも一方の投球方向（RightまたはLeft）を選択してください。")
            df = pd.DataFrame()  # 空のDataFrameを設定
            return
        if len(df) == 0:
            st.warning("該当するデータがありません。")
            return
        #日付でクエリ
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        # 日付が正しく変換されなかった行を除外
        df = df.dropna(subset=["Date"])
        min_date = df["Date"].min().to_pydatetime()
        max_date = df["Date"].max().to_pydatetime()
        selected_date_range = st.slider("日付範囲を選択", min_value=min_date, max_value=max_date,
                                        value=(min_date, max_date), format="YYYY-MM-DD")
        df = df[(df["Date"] >= selected_date_range[0]) & (df["Date"] <= selected_date_range[1])]

        stats_df = compute_batter_stats(df)
        st.subheader("選手ごとの成績")
        st.dataframe(stats_df)
    except Exception as e:
        st.error("成績集計に失敗しました")
        st.exception(e)


if __name__ == "__main__":
    main()



