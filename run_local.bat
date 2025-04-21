@echo off
echo 筋トレレビューアプリを起動します...

REM 仮想環境が存在するかチェック
if not exist "venv" (
    echo 仮想環境を作成しています...
    python -m venv venv
)

REM 仮想環境を有効化
call venv\Scripts\activate

REM 依存パッケージのインストール
echo 依存パッケージを確認しています...
pip install -r requirements.txt

REM Streamlitアプリの起動
echo アプリを起動しています...
streamlit run app.py

pause 