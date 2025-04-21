import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# アプリのタイトルとテーマ設定（最初のStreamlitコマンドとして配置）
st.set_page_config(
    page_title="筋トレレビューアプリ",
    page_icon="💪",
    layout="wide",
)

# Supabaseの設定
try:
    from supabase import create_client
    load_dotenv()
    
    supabase_url = os.environ.get('url') or os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('key') or os.environ.get('SUPABASE_KEY')
    
    # 環境変数がない場合はStreamlit secretsを使用
    if not supabase_url or not supabase_key:
        try:
            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]
        except Exception as e:
            st.error(f"シークレット読み込みエラー: {str(e)}")
    
    # Supabaseクライアントを作成（プロキシ設定なし）
    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
        except Exception as e:
            st.error(f"Supabase初期化エラー: {str(e)}")
            db_connected = False
    else:
        st.error("Supabase URL または Key が設定されていません")
        db_connected = False
    
    # データベース接続のテスト - 修正版
    try:
        try:
            response = supabase.table('training_records').select('id').limit(1).execute()
            if hasattr(response, 'data'):
                db_connected = True
            else:
                if isinstance(response, dict) and 'data' in response:
                    db_connected = True
                else:
                    db_connected = False
                    st.error(f"予期しないレスポンス形式: {type(response)}")
        except AttributeError as attr_error:
            db_connected = False
            st.error(f"属性エラー: {str(attr_error)}")
    except Exception as conn_error:
        db_connected = False
        st.error(f"テーブル接続エラー: {str(conn_error)}")
except Exception as e:
    db_connected = False
    st.error(f"データベース接続エラー: {str(e)}")

st.title("💪 筋トレレビューアプリ")

# サイドバーでの機能選択
selected_function = st.sidebar.radio(
    "機能選択",
    ["トレーニング記録の入力", "過去の記録 (リスト表示)", "過去の記録 (グラフ表示)", "成長フィードバック"]
)

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
            exercise_name = st.text_input("種目名", placeholder="例: ベンチプレス")
            weight = st.number_input("重量 (kg)", min_value=0.0, step=0.5, format="%.1f")
        
        with col2:
            reps = st.number_input("回数 (reps)", min_value=1, step=1)
            sets = st.number_input("セット数 (sets)", min_value=1, step=1)
            notes = st.text_area("メモ (任意)", placeholder="調子や感想など")
        
        submit_button = st.form_submit_button("記録を保存")
    
    # フォーム送信時の処理
    if submit_button:
        if not exercise_name:
            st.error("種目名を入力してください。")
        elif db_connected:
            try:
                # Supabaseにデータを保存
                data = {
                    "training_date": str(training_date),
                    "exercise_name": exercise_name,
                    "weight": float(weight),
                    "reps": int(reps),
                    "sets": int(sets),
                    "notes": notes
                }
                
                response = supabase.table('training_records').insert(data).execute()
                
                if hasattr(response, 'data') and len(response.data) > 0:
                    st.success("トレーニング記録が正常に保存されました！")
                    st.session_state.last_saved_record = data  # セッションに保存
                else:
                    st.error("データの保存に失敗しました。")
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
        else:
            st.error("データベース接続がありません。設定を確認してください。")

# 過去の記録 (リスト表示) 機能
elif selected_function == "過去の記録 (リスト表示)":
    st.header("過去のトレーニング記録")
    
    if db_connected:
        try:
            # フィルタリングオプション
            col1, col2 = st.columns(2)
            
            with col1:
                # 日付範囲選択
                start_date = datetime.now().date() - timedelta(days=30)
                end_date = datetime.now().date()
                
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("開始日", value=start_date, max_value=end_date)
                with col_end:
                    end_date = st.date_input("終了日", value=end_date)
            
            with col2:
                # 種目名でのフィルタリング
                response = supabase.table('training_records').select('exercise_name').execute()
                all_exercises = list(set([record['exercise_name'] for record in response.data]))
                
                selected_exercise = st.selectbox(
                    "種目で絞り込み",
                    options=["すべての種目"] + sorted(all_exercises)
                )
            
            # データの取得
            query = supabase.table('training_records').select('*')
            
            # 日付フィルター
            # start_dateとend_dateは既に上で定義されているので直接使用
            query = query.gte('training_date', str(start_date)).lte('training_date', str(end_date))
            
            # 種目フィルター
            if selected_exercise != "すべての種目":
                query = query.eq('exercise_name', selected_exercise)
            
            # 実行と結果取得
            response = query.order('training_date', desc=True).execute()
            
            if hasattr(response, 'data') and len(response.data) > 0:
                # データをDataFrameに変換
                df = pd.DataFrame(response.data)
                df['training_date'] = pd.to_datetime(df['training_date']).dt.date
                
                # 表示するカラムを整理
                display_columns = [
                    'training_date', 'exercise_name', 'weight', 'reps', 'sets', 'notes'
                ]
                
                st.dataframe(
                    df[display_columns].style.format({
                        'weight': '{:.1f} kg',
                        'reps': '{} 回',
                        'sets': '{} セット'
                    }),
                    use_container_width=True
                )
                
                st.info(f"全 {len(df)} 件のレコードが見つかりました。")
            else:
                st.info("条件に一致するレコードがありません。")
        except Exception as e:
            st.error(f"データの取得中にエラーが発生しました: {str(e)}")
    else:
        st.error("データベース接続がありません。設定を確認してください。")

# 過去の記録 (グラフ表示) 機能
elif selected_function == "過去の記録 (グラフ表示)":
    st.header("トレーニング記録の推移")
    
    if db_connected:
        try:
            # 種目選択
            response = supabase.table('training_records').select('exercise_name').execute()
            all_exercises = list(set([record['exercise_name'] for record in response.data]))
            
            if not all_exercises:
                st.info("まだトレーニング記録がありません。「トレーニング記録の入力」から記録を追加してください。")
            else:
                selected_exercise = st.selectbox(
                    "種目を選択",
                    options=sorted(all_exercises)
                )
                
                # データ取得
                response = supabase.table('training_records')\
                    .select('*')\
                    .eq('exercise_name', selected_exercise)\
                    .order('training_date', desc=False)\
                    .execute()
                
                if hasattr(response, 'data') and len(response.data) > 0:
                    # データをDataFrameに変換
                    df = pd.DataFrame(response.data)
                    df['training_date'] = pd.to_datetime(df['training_date'])
                    
                    # グラフ表示モード選択
                    graph_mode = st.radio(
                        "グラフ表示モード",
                        ["重量の推移", "回数の推移", "ボリューム(重量×回数×セット)の推移"]
                    )
                    
                    if graph_mode == "重量の推移":
                        fig = px.line(
                            df, 
                            x='training_date', 
                            y='weight',
                            markers=True,
                            title=f"{selected_exercise}の重量推移"
                        )
                        fig.update_layout(
                            xaxis_title="日付",
                            yaxis_title="重量 (kg)",
                            yaxis=dict(rangemode='tozero')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    elif graph_mode == "回数の推移":
                        fig = px.line(
                            df, 
                            x='training_date', 
                            y='reps',
                            markers=True,
                            title=f"{selected_exercise}の回数推移"
                        )
                        fig.update_layout(
                            xaxis_title="日付",
                            yaxis_title="回数 (reps)",
                            yaxis=dict(rangemode='tozero')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    elif graph_mode == "ボリューム(重量×回数×セット)の推移":
                        # ボリュームの計算
                        df['volume'] = df['weight'] * df['reps'] * df['sets']
                        
                        fig = px.line(
                            df, 
                            x='training_date', 
                            y='volume',
                            markers=True,
                            title=f"{selected_exercise}のトレーニングボリューム推移"
                        )
                        fig.update_layout(
                            xaxis_title="日付",
                            yaxis_title="ボリューム (kg×reps×sets)",
                            yaxis=dict(rangemode='tozero')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 統計情報
                    st.subheader("統計情報")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        max_weight = df['weight'].max()
                        st.metric("自己ベスト重量", f"{max_weight:.1f} kg")
                    
                    with col2:
                        max_reps = df['reps'].max()
                        st.metric("自己ベスト回数", f"{max_reps} 回")
                    
                    with col3:
                        if 'volume' not in df.columns:
                            df['volume'] = df['weight'] * df['reps'] * df['sets']
                        max_volume = df['volume'].max()
                        st.metric("最大ボリューム", f"{max_volume:.1f}")
                    
                    # データテーブル表示
                    with st.expander("詳細データを表示"):
                        st.dataframe(
                            df.sort_values('training_date', ascending=False)[['training_date', 'weight', 'reps', 'sets', 'notes']],
                            use_container_width=True
                        )
                else:
                    st.info(f"{selected_exercise}の記録がありません。")
        except Exception as e:
            st.error(f"グラフ表示中にエラーが発生しました: {str(e)}")
    else:
        st.error("データベース接続がありません。設定を確認してください。")

# 成長フィードバック機能
elif selected_function == "成長フィードバック":
    st.header("成長フィードバック 💪")
    
    if db_connected:
        try:
            # ユーザーが今日のトレーニングを見るボタンを押した場合
            if st.button("今日のトレーニング結果を見る"):
                # 今日の日付を取得
                today = datetime.now().date()
                
                # 今日のトレーニング記録を取得
                today_response = supabase.table('training_records')\
                    .select('*')\
                    .eq('training_date', today.isoformat())\
                    .execute()
                
                if hasattr(today_response, 'data') and len(today_response.data) > 0:
                    # 今日のトレーニング記録がある場合
                    today_records = today_response.data
                    
                    st.success(f"今日は{len(today_records)}種目のトレーニングを記録しました！")
                    
                    # 各種目についてフィードバック表示
                    for record in today_records:
                        exercise = record['exercise_name']
                        weight = record['weight']
                        reps = record['reps']
                        
                        # 前回の同じ種目の記録を取得
                        previous_response = supabase.table('training_records')\
                            .select('*')\
                            .eq('exercise_name', exercise)\
                            .lt('training_date', today.isoformat())\
                            .order('training_date', desc=True)\
                            .limit(1)\
                            .execute()
                        
                        # 自己ベスト（重量）の記録を取得
                        best_weight_response = supabase.table('training_records')\
                            .select('*')\
                            .eq('exercise_name', exercise)\
                            .neq('training_date', today.isoformat())\
                            .order('weight', desc=True)\
                            .limit(1)\
                            .execute()
                        
                        # 自己ベスト（回数）の記録を取得
                        best_reps_response = supabase.table('training_records')\
                            .select('*')\
                            .eq('exercise_name', exercise)\
                            .neq('training_date', today.isoformat())\
                            .order('reps', desc=True)\
                            .limit(1)\
                            .execute()
                        
                        # 前回の記録と比較
                        has_previous = hasattr(previous_response, 'data') and len(previous_response.data) > 0
                        has_best_weight = hasattr(best_weight_response, 'data') and len(best_weight_response.data) > 0
                        has_best_reps = hasattr(best_reps_response, 'data') and len(best_reps_response.data) > 0
                        
                        # 結果表示用のコンテナ
                        with st.container():
                            st.subheader(f"🔍 {exercise}")
                            
                            col1, col2 = st.columns(2)
                            
                            # 重量のフィードバック
                            with col1:
                                if has_previous:
                                    prev_weight = previous_response.data[0]['weight']
                                    weight_diff = weight - prev_weight
                                    
                                    if weight_diff > 0:
                                        st.success(f"🎉 重量アップ: +{weight_diff:.1f}kg ({prev_weight:.1f}kg → {weight:.1f}kg)")
                                    elif weight_diff < 0:
                                        st.info(f"📉 重量: {weight_diff:.1f}kg ({prev_weight:.1f}kg → {weight:.1f}kg) お疲れ様でした！")
                                    else:
                                        st.info(f"📊 重量維持: {weight:.1f}kg (前回と同じ)")
                                
                                if has_best_weight:
                                    best_weight = best_weight_response.data[0]['weight']
                                    if weight > best_weight:
                                        st.success(f"🏆 自己ベスト更新！ 重量: {best_weight:.1f}kg → {weight:.1f}kg")
                            
                            # 回数のフィードバック
                            with col2:
                                if has_previous:
                                    prev_reps = previous_response.data[0]['reps']
                                    reps_diff = reps - prev_reps
                                    
                                    if reps_diff > 0:
                                        st.success(f"💪 回数アップ: +{reps_diff}回 ({prev_reps}回 → {reps}回)")
                                    elif reps_diff < 0:
                                        st.info(f"📉 回数: {reps_diff}回 ({prev_reps}回 → {reps}回) 次回ファイト！")
                                    else:
                                        st.info(f"📊 回数維持: {reps}回 (前回と同じ)")
                                
                                if has_best_reps:
                                    best_reps = best_reps_response.data[0]['reps']
                                    if reps > best_reps:
                                        st.success(f"🏆 自己ベスト更新！ 回数: {best_reps}回 → {reps}回")
                            
                            # 初めての種目の場合
                            if not has_previous:
                                st.info(f"👏 初めての記録です！ 重量: {weight:.1f}kg, 回数: {reps}回")
                            
                            st.divider()
                else:
                    st.warning("今日のトレーニング記録が見つかりません。「トレーニング記録の入力」から今日のトレーニングを記録してください。")
            
            # 最新のトレーニング日のリンクを表示
            latest_response = supabase.table('training_records')\
                .select('training_date')\
                .order('training_date', desc=True)\
                .limit(1)\
                .execute()
            
            if hasattr(latest_response, 'data') and len(latest_response.data) > 0:
                latest_date = datetime.fromisoformat(latest_response.data[0]['training_date']).date()
                st.info(f"最新のトレーニング日: {latest_date.strftime('%Y-%m-%d')}")
        
        except Exception as e:
            st.error(f"フィードバック表示中にエラーが発生しました: {str(e)}")
    else:
        st.error("データベース接続がありません。設定を確認してください。")

# アプリについての情報
with st.sidebar.expander("アプリについて"):
    st.write("""
    **筋トレレビューアプリ**
    
    自分のトレーニング記録を管理し、進捗を可視化することで
    モチベーションを維持するためのアプリです。
    
    - トレーニング内容の記録
    - 過去の記録の確認
    - 成長の可視化とフィードバック
    """)

# データベース接続状態の表示
with st.sidebar:
    if db_connected:
        st.success("✅ データベース接続: OK")
    else:
        st.error("❌ データベース接続: エラー")                    