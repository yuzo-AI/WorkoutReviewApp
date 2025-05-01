# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

# --- YouTube API関連のインポートを追加 ---
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# --- ここまで追加 ---

# アプリのタイトルとテーマ設定（最初のStreamlitコマンドとして配置）
st.set_page_config(
    page_title="筋トレレビューアプリ",
    page_icon="💪",
    layout="wide",
)

# --- セッション状態の初期化 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False

# --- Supabaseクライアントの初期化と接続テスト ---
supabase = None
db_connected = False
supabase_error_message = ""
try:
    from supabase import create_client
    load_dotenv() # ローカルでの.envファイル読み込み用

    supabase_url = os.environ.get('url') or os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('key') or os.environ.get('SUPABASE_KEY')

    # 環境変数がない場合はStreamlit secretsを使用 (Cloudデプロイ用)
    if not supabase_url or not supabase_key:
        try:
            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]
        except Exception as e:
            # secretsがない場合のエラーは初期段階では許容するかもしれない
            pass # st.error(f"シークレット読み込みエラー: {str(e)}")

    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            # 簡単な接続テスト
            response = supabase.table('training_records').select('id').limit(1).execute()
            db_connected = True # ここまで来たらOKとする
        except Exception as conn_error:
            supabase_error_message = f"データベースへの接続/テーブルアクセスに失敗しました: {str(conn_error)}"
            db_connected = False
    else:
        supabase_error_message = "Supabase URL または Key が設定されていません。"
        db_connected = False

except ImportError:
    supabase_error_message = "Supabaseライブラリが見つかりません。'pip install supabase-py' を実行してください。"
    db_connected = False
except Exception as e:
    supabase_error_message = f"Supabase初期化中に予期せぬエラーが発生しました: {str(e)}"
    db_connected = False

# --- YouTube APIキーの読み込み ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
# --- ここまで追加 ---


# --- サンプルデータ生成関数 ---
def create_sample_data():
    # (省略 - 前回のコードと同じ)
    import pandas as pd
    from datetime import datetime, timedelta
    import random

    exercises = ["ベンチプレス", "スクワット", "デッドリフト", "懸垂", "腕立て伏せ"]
    data = []
    today = datetime.now().date()
    for i in range(30):
        date = today - timedelta(days=i)
        for exercise in exercises[:random.randint(1, 3)]:
            if random.random() < 0.7:
                weight_base = {"ベンチプレス": 60, "スクワット": 80, "デッドリフト": 100, "懸垂": 0, "腕立て伏せ": 0}
                reps_base = {"ベンチプレス": 8, "スクワット": 8, "デッドリフト": 6, "懸垂": 10, "腕立て伏せ": 15}
                progress_factor = max(0, (30 - i) / 30 * 0.2)
                data.append({
                    "id": f"sample-{i}-{exercise}",
                    "training_date": date,
                    "exercise_name": exercise,
                    "weight": round(weight_base[exercise] * (1 + progress_factor) + random.uniform(-2, 2), 1),
                    "reps": int(reps_base[exercise] + random.randint(-2, 2)),
                    "sets": random.randint(3, 5),
                    "notes": "サンプルデータ"
                })
    df = pd.DataFrame(data)
    # weightが数値型であることを確認
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    df = df.dropna(subset=['weight']) # 数値でない行を削除
    return df


# --- 認証関連関数 ---
def sign_up(email, password):
    # (省略 - 前回のコードと同じ)
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if hasattr(response, 'user') and response.user:
            return True, response.user.id, response.user.email
        elif isinstance(response, dict) and 'user' in response and response['user']:
             return True, response['user']['id'], response['user']['email']
        else: # APIエラーなど
             error_message = getattr(response, 'message', '不明なエラー')
             st.error(f"サインアップエラー: {error_message}")
             return False, None, None
    except Exception as e:
        st.error(f"サインアップ中に予期せぬエラー: {str(e)}")
        return False, None, None

def sign_in(email, password):
    # (省略 - 前回のコードと同じ)
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if hasattr(response, 'user') and response.user:
            return True, response.user.id, response.user.email
        elif isinstance(response, dict) and 'user' in response and response['user']:
             return True, response['user']['id'], response['user']['email']
        else: # APIエラーなど (例: Invalid login credentials)
             error_message = getattr(response, 'message', '不明なエラー')
             st.error(f"ログインエラー: {error_message}")
             return False, None, None
    except Exception as e:
        st.error(f"ログイン中に予期せぬエラー: {str(e)}")
        return False, None, None


def sign_out():
    # (省略 - 前回のコードと同じ)
    try:
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.is_guest = False
        # 他のセッション状態もクリアするならここ
        return True
    except Exception as e:
        st.error(f"ログアウトエラー: {str(e)}")
        return False

def guest_login():
    # (省略 - 前回のコードと同じ)
    st.session_state.authenticated = True
    st.session_state.is_guest = True
    st.session_state.user_id = None
    st.session_state.user_email = "ゲスト"
    return True

# --- YouTube検索関数 ---
def search_youtube_videos(query, max_results=3):
    if not YOUTUBE_API_KEY:
        st.warning("YouTube APIキーが設定されていないため、動画検索は利用できません。")
        return []
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        search_response = youtube.search().list(
            q=f"{query} フォーム やり方 解説", # より具体的な検索クエリ
            part='snippet',
            maxResults=max_results,
            type='video',
            videoEmbeddable='true', # 埋め込み可能な動画を優先
            order='relevance' # 関連性の高い順
        ).execute()

        videos = []
        for search_result in search_response.get('items', []):
            # サムネイルURLが存在するか確認
            thumbnail_url = search_result['snippet']['thumbnails'].get('default', {}).get('url')
            if thumbnail_url: # サムネイルがあるものだけ追加（任意）
                videos.append({
                    'title': search_result['snippet']['title'],
                    'videoId': search_result['id']['videoId'],
                    'thumbnail': thumbnail_url
                })
        return videos
    except HttpError as e:
        # APIクォータ超過などのエラーをより分かりやすく表示
        error_details = json.loads(e.content.decode('utf-8')).get('error', {}).get('errors', [{}])[0]
        reason = error_details.get('reason', '不明な理由')
        message = error_details.get('message', str(e))
        st.error(f"YouTube APIエラー ({reason}): {message}")
        return []
    except Exception as e:
        st.error(f"YouTube検索中に予期せぬエラーが発生しました: {str(e)}")
        return []
# --- ここまで追加 ---


st.title("💪 筋トレレビューアプリ")

# --- ログイン/サインアップ処理 ---
if not st.session_state.authenticated:
    # (省略 - 前回のコードと同じ)
    st.info("続行するにはログインまたはサインアップしてください。")
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    with tab1:
        with st.form("login_form"):
            login_email = st.text_input("メールアドレス", key="login_email")
            login_password = st.text_input("パスワード", type="password", key="login_password")
            login_submit = st.form_submit_button("ログイン")
            if login_submit:
                if login_email and login_password:
                    success, user_id, user_email = sign_in(login_email, login_password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_id
                        st.session_state.user_email = user_email
                        st.session_state.is_guest = False
                        st.success("ログインに成功しました！")
                        st.rerun()
                else:
                    st.warning("メールアドレスとパスワードを入力してください。")

    with tab2:
         with st.form("signup_form"):
            signup_email = st.text_input("メールアドレス", key="signup_email")
            signup_password = st.text_input("パスワード", type="password", key="signup_password")
            signup_password_confirm = st.text_input("パスワード（確認）", type="password", key="signup_password_confirm")
            signup_submit = st.form_submit_button("登録")
            if signup_submit:
                if signup_email and signup_password and signup_password_confirm:
                    if signup_password == signup_password_confirm:
                        if len(signup_password) >= 6:
                             success, user_id, user_email = sign_up(signup_email, signup_password)
                             if success:
                                st.session_state.authenticated = True
                                st.session_state.user_id = user_id
                                st.session_state.user_email = user_email
                                st.session_state.is_guest = False
                                st.success("アカウントが正常に作成されました！ログインしてください。") # 登録後はログインを促す
                                # st.rerun() # 自動でログインさせない方が一般的かも
                        else:
                            st.error("パスワードは6文字以上である必要があります。")
                    else:
                        st.error("パスワードが一致しません。")
                else:
                    st.error("すべてのフィールドを入力してください。")

    if st.button("ゲストとして試用する"):
        guest_login()
        st.success("ゲストモードでログインしました。記録の保存や過去データの閲覧はできません。")
        st.rerun()

    # DB接続エラーがあれば表示
    if not db_connected and supabase_error_message:
        st.error(f"データベース初期接続エラー: {supabase_error_message}")

    st.stop() # 認証されていない場合はここで処理を停止

# --- アプリケーションメイン部分 ---

# サイドバーにユーザー情報とログアウトボタン
with st.sidebar:
    if st.session_state.authenticated:
        st.write(f"ログイン中: {st.session_state.user_email}")
        if st.button("ログアウト"):
            if sign_out():
                st.success("ログアウトしました。")
                st.rerun() # ログアウト後に画面を更新

    # DB接続状態表示
    if db_connected:
        st.success("✅ データベース接続: OK")
    else:
        st.error("❌ データベース接続: エラー")
        if supabase_error_message:
             st.caption(f"エラー詳細: {supabase_error_message}")

    st.divider()
    selected_function = st.radio(
        "機能選択",
        ["トレーニング記録の入力", "過去の記録 (リスト表示)", "過去の記録 (グラフ表示)", "成長フィードバック"]
    )
    st.divider()
    with st.expander("アプリについて"):
        # (省略 - 前回のコードと同じ)
        st.write("""
        **筋トレレビューアプリ**

        自分のトレーニング記録を管理し、進捗を可視化することで
        モチベーションを維持するためのアプリです。

        - トレーニング内容の記録
        - 過去の記録の確認
        - 成長の可視化とフィードバック
        - 参考フォーム動画の検索
        """)


# --- 機能ごとの表示 ---

# トレーニング記録の入力機能
if selected_function == "トレーニング記録の入力":
    st.header("トレーニング記録の入力")

    with st.form("training_form"):
        col1, col2 = st.columns(2)

        with col1:
            training_date = st.date_input(
                "トレーニング日",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
            exercise_name = st.text_input("種目名", placeholder="例: ベンチプレス", key="exercise_input") # keyを追加
            weight = st.number_input("重量 (kg)", min_value=0.0, step=0.5, format="%.1f")

        with col2:
            reps = st.number_input("回数 (reps)", min_value=1, step=1)
            sets = st.number_input("セット数 (sets)", min_value=1, step=1)
            notes = st.text_area("メモ (任意)", placeholder="調子や感想など")

        submit_button = st.form_submit_button("記録を保存")

    # --- YouTube動画検索UIを追加 ---
    current_exercise = st.session_state.get("exercise_input", "") # text_inputの値を取得
    if current_exercise and not st.session_state.is_guest: # 種名があり、ゲストでない場合
        if st.button(f"「{current_exercise}」のフォーム動画を探す", key=f"search_{current_exercise}"):
            with st.spinner("動画を検索中..."):
                videos = search_youtube_videos(current_exercise)
                if videos:
                    st.write("---")
                    st.subheader("💡 参考フォーム動画")
                    # --- 表示方法を改善 ---
                    num_videos = len(videos)
                    cols = st.columns(num_videos) # 結果の数だけ列を作成
                    for i, video in enumerate(videos):
                        with cols[i]:
                            st.image(video['thumbnail'], use_column_width=True)
                            st.caption(video['title']) # 画像の下にタイトル
                            # 動画埋め込み（複数埋め込むと重い場合があるので注意）
                            with st.expander("動画を再生"): # Expanderに入れる
                                st.video(f"https://www.youtube.com/watch?v={video['videoId']}")
                            st.link_button("YouTubeで見る", f"https://www.youtube.com/watch?v={video['videoId']}")
                    st.write("---")
                    # --- ここまで改善 ---
                else:
                    st.info("参考動画が見つかりませんでした。検索語句を変えてみてください。")
    # --- ここまで追加 ---

    # フォーム送信時の処理
    if submit_button:
        # (省略 - 前回のコードと同じ、ゲストチェックとuser_id挿入は含む)
        if not exercise_name:
            st.error("種目名を入力してください。")
        elif db_connected:
            try:
                data = {
                    "training_date": str(training_date), # 文字列で保存
                    "exercise_name": exercise_name,
                    "weight": float(weight),
                    "reps": int(reps),
                    "sets": int(sets),
                    "notes": notes
                }
                if st.session_state.is_guest:
                    st.warning("ゲストモードではデータを保存できません。登録してログインすると、トレーニング記録を保存できます。")
                    # st.session_state.last_saved_record = data # ゲスト用の一時保存は不要かも
                    st.info("ゲストモードでの記録をシミュレートしました（保存されません）。")
                elif st.session_state.user_id: # user_idがあるか確認
                    data["user_id"] = st.session_state.user_id
                    response = supabase.table('training_records').insert(data).execute()
                    if response.data and len(response.data) > 0:
                        st.success("トレーニング記録が正常に保存されました！")
                    else:
                         error_detail = getattr(response, 'error', None)
                         st.error(f"データの保存に失敗しました。{f'エラー: {error_detail}' if error_detail else ''}")
                else:
                     st.error("ログインユーザー情報が見つかりません。再度ログインしてください。") # user_idがない場合
            except Exception as e:
                st.error(f"データ保存中にエラーが発生しました: {str(e)}")
        else:
            st.error("データベースに接続できません。設定を確認してください。")


# --- 過去の記録 (リスト表示) 機能 ---
elif selected_function == "過去の記録 (リスト表示)":
    # (省略 - 前回のコードと同じ、ゲストチェックとuser_idフィルタは含む)
    st.header("過去のトレーニング記録")
    if db_connected:
        try:
            col1, col2 = st.columns(2)
            with col1:
                start_date_default = datetime.now().date() - timedelta(days=30)
                end_date_default = datetime.now().date()
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("開始日", value=start_date_default, max_value=end_date_default)
                with col_end:
                    end_date = st.date_input("終了日", value=end_date_default, min_value=start_date) # min_value追加

            with col2:
                try:
                    # ログインユーザーの種目リストのみ取得
                    query = supabase.table('training_records').select('exercise_name')
                    if not st.session_state.is_guest and st.session_state.user_id:
                        query = query.eq('user_id', st.session_state.user_id)
                    response_exercises = query.execute()

                    if response_exercises.data:
                        all_exercises = list(set([record['exercise_name'] for record in response_exercises.data if record.get('exercise_name')]))
                    else:
                        all_exercises = []
                except Exception as ex_e:
                    st.warning(f"種目リストの取得に失敗しました: {ex_e}")
                    all_exercises = []
                selected_exercise = st.selectbox("種目で絞り込み", options=["すべての種目"] + sorted(all_exercises))

            if st.session_state.is_guest:
                st.info("ゲストモードではサンプルデータが表示されます。")
                sample_df_list = create_sample_data()
                # 日付と種目でフィルタ
                sample_df_list['training_date'] = pd.to_datetime(sample_df_list['training_date']).dt.date
                sample_df_list = sample_df_list[
                    (sample_df_list['training_date'] >= start_date) &
                    (sample_df_list['training_date'] <= end_date)
                ]
                if selected_exercise != "すべての種目":
                    sample_df_list = sample_df_list[sample_df_list['exercise_name'] == selected_exercise]

                if not sample_df_list.empty:
                     display_columns_guest = ['training_date', 'exercise_name', 'weight', 'reps', 'sets', 'notes']
                     display_columns_guest = [col for col in display_columns_guest if col in sample_df_list.columns]
                     st.dataframe(
                         sample_df_list[display_columns_guest].style.format({
                             'weight': '{:.1f} kg', 'reps': '{} 回', 'sets': '{} セット'
                         }), use_container_width=True
                     )
                     st.info(f"サンプルデータ {len(sample_df_list)} 件")
                else:
                     st.info("条件に合うサンプルデータがありません。")

            elif st.session_state.user_id: # ログインユーザー
                query = supabase.table('training_records').select('*')
                query = query.eq('user_id', st.session_state.user_id)
                query = query.gte('training_date', str(start_date)).lte('training_date', str(end_date))
                if selected_exercise != "すべての種目":
                    query = query.eq('exercise_name', selected_exercise)
                response = query.order('training_date', desc=True).execute()

                if response.data and len(response.data) > 0:
                    df = pd.DataFrame(response.data)
                    if 'notes' not in df.columns: df['notes'] = ""
                    else: df['notes'] = df['notes'].fillna("")
                    df['training_date'] = pd.to_datetime(df['training_date']).dt.date
                    display_columns = ['training_date', 'exercise_name', 'weight', 'reps', 'sets', 'notes']
                    display_columns = [col for col in display_columns if col in df.columns]
                    st.dataframe(
                        df[display_columns].style.format({
                            'weight': '{:.1f} kg', 'reps': '{} 回', 'sets': '{} セット'
                        }), use_container_width=True
                    )
                    st.info(f"全 {len(df)} 件のレコードが見つかりました。")
                else:
                    st.info("条件に一致するレコードがありません。")
            else:
                 st.warning("ユーザー情報が見つかりません。")
        except Exception as e:
            st.error(f"データの取得中にエラーが発生しました: {str(e)}")
    else:
        st.error("データベースに接続できません。設定を確認してください。")


# --- 過去の記録 (グラフ表示) 機能 ---
elif selected_function == "過去の記録 (グラフ表示)":
    # (省略 - 前回のコードと同じ構成、ゲストチェックとuser_idフィルタは含む)
    st.header("トレーニング記録の推移")
    if db_connected:
        try:
            # 種目選択
            try:
                query = supabase.table('training_records').select('exercise_name')
                if not st.session_state.is_guest and st.session_state.user_id:
                    query = query.eq('user_id', st.session_state.user_id)
                response_exercises = query.execute()
                if response_exercises.data:
                    all_exercises = list(set([record['exercise_name'] for record in response_exercises.data if record.get('exercise_name')]))
                else:
                    all_exercises = []
            except Exception as ex_e:
                st.warning(f"種目リストの取得に失敗しました: {ex_e}")
                all_exercises = []

            if not all_exercises and not st.session_state.is_guest:
                 st.info("まだトレーニング記録がありません。「トレーニング記録の入力」から記録を追加してください。")
            else:
                if st.session_state.is_guest:
                     all_exercises = ["ベンチプレス", "スクワット", "デッドリフト", "懸垂", "腕立て伏せ"] # ゲスト用サンプル種目
                selected_exercise = st.selectbox("種目を選択", options=sorted(all_exercises))

                # データ取得
                df = None
                if st.session_state.is_guest:
                    st.info("ゲストモードではサンプルデータが表示されます。")
                    sample_df_graph = create_sample_data()
                    df = sample_df_graph[sample_df_graph['exercise_name'] == selected_exercise].copy() # .copy()推奨
                    if not df.empty:
                        df['training_date'] = pd.to_datetime(df['training_date']) # 日付型に変換
                elif st.session_state.user_id:
                    response = supabase.table('training_records')\
                        .select('*')\
                        .eq('user_id', st.session_state.user_id)\
                        .eq('exercise_name', selected_exercise)\
                        .order('training_date', desc=False)\
                        .execute()
                    if response.data and len(response.data) > 0:
                         df = pd.DataFrame(response.data)
                         df['training_date'] = pd.to_datetime(df['training_date'])

                if df is not None and not df.empty:
                    # データ型の確認と変換
                    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
                    df['reps'] = pd.to_numeric(df['reps'], errors='coerce')
                    df['sets'] = pd.to_numeric(df['sets'], errors='coerce')
                    df = df.dropna(subset=['weight', 'reps', 'sets']) # 不正データを削除

                    if not df.empty: # データが残っているか確認
                        graph_mode = st.radio("グラフ表示モード", ["重量の推移", "回数の推移", "ボリューム(重量×回数×セット)の推移"])

                        try:
                            if graph_mode == "重量の推移":
                                fig = px.line(df, x='training_date', y='weight', markers=True, title=f"{selected_exercise}の重量推移")
                                fig.update_layout(xaxis_title="日付", yaxis_title="重量 (kg)", yaxis=dict(rangemode='tozero'))
                                st.plotly_chart(fig, use_container_width=True)
                            elif graph_mode == "回数の推移":
                                fig = px.line(df, x='training_date', y='reps', markers=True, title=f"{selected_exercise}の回数推移")
                                fig.update_layout(xaxis_title="日付", yaxis_title="回数 (reps)", yaxis=dict(rangemode='tozero'))
                                st.plotly_chart(fig, use_container_width=True)
                            elif graph_mode == "ボリューム(重量×回数×セット)の推移":
                                df['volume'] = df['weight'] * df['reps'] * df['sets']
                                fig = px.line(df, x='training_date', y='volume', markers=True, title=f"{selected_exercise}のトレーニングボリューム推移")
                                fig.update_layout(xaxis_title="日付", yaxis_title="ボリューム (kg×reps×sets)", yaxis=dict(rangemode='tozero'))
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as plot_e:
                            st.error(f"グラフ描画エラー: {plot_e}")

                        # 統計情報
                        st.subheader("統計情報")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            max_weight = df['weight'].max()
                            st.metric("自己ベスト重量", f"{max_weight:.1f} kg" if pd.notna(max_weight) else "N/A")
                        with col2:
                            max_reps = df['reps'].max()
                            st.metric("自己ベスト回数", f"{int(max_reps)} 回" if pd.notna(max_reps) else "N/A")
                        with col3:
                            if 'volume' not in df.columns: df['volume'] = df['weight'] * df['reps'] * df['sets']
                            max_volume = df['volume'].max()
                            st.metric("最大ボリューム", f"{max_volume:.1f}" if pd.notna(max_volume) else "N/A")

                        # データテーブル表示
                        with st.expander("詳細データを表示"):
                            display_cols_detail_graph = ['training_date', 'weight', 'reps', 'sets', 'notes']
                            display_cols_detail_graph = [col for col in display_cols_detail_graph if col in df.columns]
                            st.dataframe(
                                df.sort_values('training_date', ascending=False)[display_cols_detail_graph],
                                use_container_width=True
                            )
                    else:
                         st.info(f"{selected_exercise}の有効な記録がありません。")
                else:
                    st.info(f"{selected_exercise}の記録がありません。")

        except Exception as e:
            st.error(f"グラフ表示機能で予期せぬエラーが発生しました: {str(e)}")
    else:
        st.error("データベースに接続できません。設定を確認してください。")


# --- 成長フィードバック機能 ---
elif selected_function == "成長フィードバック":
    # (省略 - 前回のコードと同じ、ゲストチェックとuser_idフィルタは含む)
    st.header("成長フィードバック 💪")
    if db_connected:
        try:
            if st.button("今日のトレーニング結果を見る"):
                today = datetime.now().date()

                if st.session_state.is_guest:
                    st.info("ゲストモードではサンプルフィードバックが表示されます。")
                    st.success("🎉 ベンチプレス 重量 +2.5kg (60kg -> 62.5kg)")
                    st.success("💪 スクワット 回数 +2回 (8回 -> 10回)")
                elif st.session_state.user_id:
                    today_response = supabase.table('training_records')\
                        .select('*')\
                        .eq('user_id', st.session_state.user_id)\
                        .eq('training_date', today.isoformat())\
                        .execute()

                    if today_response.data and len(today_response.data) > 0:
                        today_records = today_response.data
                        st.success(f"今日は{len(today_records)}種目のトレーニングを記録しました！")

                        for record in today_records:
                            exercise = record.get('exercise_name', 'N/A')
                            weight = pd.to_numeric(record.get('weight'), errors='coerce')
                            reps = pd.to_numeric(record.get('reps'), errors='coerce')

                            if pd.isna(weight) or pd.isna(reps): continue # 数値でないデータはスキップ

                            # 前回記録
                            previous_response = supabase.table('training_records')\
                                .select('*')\
                                .eq('user_id', st.session_state.user_id)\
                                .eq('exercise_name', exercise)\
                                .lt('training_date', today.isoformat())\
                                .order('training_date', desc=True)\
                                .limit(1).execute()
                            # 自己ベスト
                            best_weight_response = supabase.table('training_records')\
                                .select('weight').eq('user_id', st.session_state.user_id)\
                                .eq('exercise_name', exercise).neq('training_date', today.isoformat())\
                                .order('weight', desc=True, nulls_last=True).limit(1).execute()
                            best_reps_response = supabase.table('training_records')\
                                .select('reps').eq('user_id', st.session_state.user_id)\
                                .eq('exercise_name', exercise).neq('training_date', today.isoformat())\
                                .order('reps', desc=True, nulls_last=True).limit(1).execute()

                            has_previous = previous_response.data and len(previous_response.data) > 0
                            has_best_weight = best_weight_response.data and len(best_weight_response.data) > 0
                            has_best_reps = best_reps_response.data and len(best_reps_response.data) > 0

                            with st.container(border=True): # 枠線を追加
                                st.subheader(f"🔍 {exercise}")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**重量**")
                                    if has_previous:
                                        prev_weight = pd.to_numeric(previous_response.data[0].get('weight'), errors='coerce')
                                        if pd.notna(prev_weight):
                                            weight_diff = weight - prev_weight
                                            if weight_diff > 0: st.success(f"🎉 +{weight_diff:.1f}kg ({prev_weight:.1f}→{weight:.1f}kg)")
                                            elif weight_diff < 0: st.info(f"📉 {weight_diff:.1f}kg ({prev_weight:.1f}→{weight:.1f}kg)")
                                            else: st.write(f"📊 維持 {weight:.1f}kg")
                                    if has_best_weight:
                                        best_weight = pd.to_numeric(best_weight_response.data[0].get('weight'), errors='coerce')
                                        if pd.notna(best_weight) and weight > best_weight:
                                            st.balloons()
                                            st.success(f"🏆 **自己ベスト更新！** ({best_weight:.1f}→{weight:.1f}kg)")
                                    elif not has_previous:
                                         st.info(f"🚀 初記録: {weight:.1f}kg")

                                with col2:
                                    st.write("**回数**")
                                    if has_previous:
                                        prev_reps = pd.to_numeric(previous_response.data[0].get('reps'), errors='coerce')
                                        if pd.notna(prev_reps):
                                            reps_diff = reps - prev_reps
                                            if reps_diff > 0: st.success(f"💪 +{int(reps_diff)}回 ({int(prev_reps)}→{int(reps)}回)")
                                            elif reps_diff < 0: st.info(f"📉 {int(reps_diff)}回 ({int(prev_reps)}→{int(reps)}回)")
                                            else: st.write(f"📊 維持 {int(reps)}回")
                                    if has_best_reps:
                                        best_reps = pd.to_numeric(best_reps_response.data[0].get('reps'), errors='coerce')
                                        if pd.notna(best_reps) and reps > best_reps:
                                             st.balloons()
                                             st.success(f"🏆 **自己ベスト更新！** ({int(best_reps)}→{int(reps)}回)")
                                    elif not has_previous:
                                         st.info(f"🚀 初記録: {int(reps)}回")
                                # st.divider() # dividerは不要かも

                    else:
                        st.warning("今日のトレーニング記録が見つかりません。「トレーニング記録の入力」から今日のトレーニングを記録してください。")
                else:
                     st.warning("ユーザー情報が見つかりません。")

            # 最新トレーニング日表示
            try:
                 if not st.session_state.is_guest and st.session_state.user_id:
                     latest_response = supabase.table('training_records')\
                         .select('training_date').eq('user_id', st.session_state.user_id)\
                         .order('training_date', desc=True).limit(1).execute()
                     if latest_response.data and len(latest_response.data) > 0:
                         latest_date_str = latest_response.data[0].get('training_date')
                         if latest_date_str:
                             latest_date = datetime.fromisoformat(latest_date_str).date()
                             st.caption(f"最新の記録日: {latest_date.strftime('%Y-%m-%d')}") # captionに変更
            except Exception as latest_e:
                 st.warning(f"最新記録日の取得エラー: {latest_e}")

        except Exception as e:
            st.error(f"フィードバック表示機能で予期せぬエラーが発生しました: {str(e)}")
    else:
        st.error("データベースに接続できません。設定を確認してください。")