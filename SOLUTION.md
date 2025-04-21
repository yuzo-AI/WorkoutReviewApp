# WorkoutReviewApp - 修正内容とDockerでの実行方法

## 修正した問題

1. **データベース接続エラー**: Supabaseクライアントのバージョン問題を修正
   - 問題: 最新のSupabaseクライアントで`proxy`パラメータに関するエラーが発生
   - 解決策: Supabaseクライアントをバージョン1.0.3にダウングレード

2. **環境変数の名前**: 環境変数`url`と`key`を正しく参照するように修正
   - 問題: コードが`SUPABASE_URL`と`SUPABASE_KEY`を参照していたが、実際には`url`と`key`として保存されていた
   - 解決策: 両方の名前をチェックするように修正し、互換性を保持

3. **Dockerコンテナに環境変数を渡す設定**: 実行スクリプトを追加
   - 問題: Dockerコンテナに環境変数を渡す方法が必要
   - 解決策: `run_docker.sh`スクリプトを作成して環境変数を安全に渡せるようにした

## Dockerでの実行方法

```bash
# イメージのビルド
docker build -t workout-review-app .

# コンテナの実行（環境変数を渡す）
docker run -p 8501:8501 \
  -e url="${url}" \
  -e key="${key}" \
  workout-review-app
```

または、同梱の実行スクリプトを使用:

```bash
chmod +x run_docker.sh
./run_docker.sh
```

## 技術的詳細

- Supabaseクライアントをバージョン1.0.3にダウングレードして`proxy`パラメータの問題を解決
- 環境変数とStreamlit secretsの両方からデータベース接続情報を取得できるように設定
- Dockerコンテナに必要な環境変数を渡す仕組みを追加
- アプリケーションはStreamlitを使用し、ポート8501で実行される
- ブラウザで http://localhost:8501 にアクセスしてアプリケーションを使用可能
