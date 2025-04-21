#!/bin/bash
echo "筋トレレビューアプリを起動します..."

# 仮想環境が存在するかチェック
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境を有効化
source venv/bin/activate

# 依存パッケージのインストール
echo "依存パッケージを確認しています..."
pip install -r requirements.txt

# Streamlitアプリの起動
echo "アプリを起動しています..."
streamlit run app.py 