# 筋トレレビューアプリ

筋力トレーニングの記録を管理し、日々の成長をゲーム感覚で可視化するWebアプリケーションです。

## 機能

- 筋トレ記録（日付、種目、重量、回数、セット数など）の入力・保存
- 過去の記録の閲覧（リスト形式・グラフ形式）
- 成長フィードバック表示（前回記録や自己ベストとの比較）

## 必要条件

- Python 3.9以上
- Supabase アカウント（無料プランで可）
- Docker（オプション、Docker環境で実行する場合）

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd muscle-training-review-app
```

### 2. Python仮想環境の作成と依存パッケージのインストール

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化（Windows）
venv\Scripts\activate
# または（macOS/Linux）
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. Supabaseの設定

1. [Supabase](https://supabase.com/)でアカウントを作成し、新しいプロジェクトを作成します。
2. `database_schema.sql`の内容をSupabaseのSQLエディタで実行し、必要なテーブルを作成します。
3. Supabaseダッシュボードから、URL（`https://xxx.supabase.co`）とAPI Key（`service_role` keyではなく`anon/public` key）を取得します。

### 4. 環境変数またはStreamlitシークレットの設定

#### 方法1: 環境変数を使用

`.env`ファイルを作成し、以下の内容を記入します：

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_api_key
```

#### 方法2: Streamlitシークレットを使用

`.streamlit`ディレクトリを作成し、その中に`secrets.toml`ファイルを作成します：

```
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

そして、`.streamlit/secrets.toml`を編集してSupabaseの認証情報を設定します。

## 実行方法

### ローカルで実行

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 を開くとアプリケーションにアクセスできます。

### Dockerで実行

```bash
# Dockerイメージのビルド
docker build -t muscle-training-app .

# コンテナの実行
docker run -p 8501:8501 muscle-training-app
```

ブラウザで http://localhost:8501 を開くとアプリケーションにアクセスできます。

## Google Cloud Runへのデプロイ

1. Google Cloudアカウントを作成し、プロジェクトを設定します。
2. Google Cloud CLIをインストールして、認証を行います。
3. 以下のコマンドでDockerイメージをビルドし、Cloud Runにデプロイします：

```bash
# プロジェクトIDを設定
PROJECT_ID=<your-google-cloud-project-id>

# Dockerイメージをビルドしてコンテナレジストリにプッシュ
gcloud builds submit --tag gcr.io/$PROJECT_ID/muscle-training-app

# Dockerイメージをデプロイ（Supabase環境変数を設定）
gcloud run deploy muscle-training-app \
  --image gcr.io/$PROJECT_ID/muscle-training-app \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "SUPABASE_URL=your_supabase_url,SUPABASE_KEY=your_supabase_api_key"
```

デプロイが完了すると、コンソールにアプリケーションのURLが表示されます。

## 注意事項

- このアプリケーションはMVPとして開発されており、最小限の機能のみを実装しています。
- 現在、ユーザー認証機能は実装されていません。将来的に追加する予定です。
- Supabase APIキーは適切に管理し、公開リポジトリに含めないようにしてください。 