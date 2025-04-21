FROM python:3.11-slim

WORKDIR /app

# パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Supabaseクライアントの特定バージョンをインストール（proxy問題を回避）
RUN pip uninstall -y supabase && pip install supabase==1.0.3

# アプリケーションのコピー
COPY . .

# ポートの公開
EXPOSE 8501

# Streamlitの実行コマンド
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]  