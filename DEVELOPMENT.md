# 開発環境セットアップガイド

## 必要な環境

- Python 3.11以上
- Poetry（Pythonパッケージ管理ツール）
- Git

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd Center_joballocation
```

### 2. Poetry のインストール

Poetryがインストールされていない場合は、以下のコマンドでインストールしてください：

```bash
# macOS/Linux/WSL
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

インストール後、パスを通す必要があります：

```bash
# ~/.bashrc, ~/.zshrc などに追加
export PATH="$HOME/.local/bin:$PATH"
```

### 3. 依存関係のインストール

```bash
# プロジェクトディレクトリで実行
poetry install
```

これにより、以下がインストールされます：
- 本番環境の依存関係（pandas, streamlit, pulp, ortools等）
- 開発環境の依存関係（pytest, black, flake8等）

### 4. 仮想環境の有効化

```bash
# Poetry シェルに入る
poetry shell

# または、コマンドの前に poetry run を付ける
poetry run python main.py
```

## 開発コマンド

### アプリケーションの起動

```bash
# Streamlitアプリの起動
poetry run streamlit run src/ui/app.py

# または Poetry shell 内で
streamlit run src/ui/app.py
```

### コード品質チェック

```bash
# コードフォーマット
poetry run black src/ tests/

# インポート順序の整理
poetry run isort src/ tests/

# リンター実行
poetry run flake8 src/ tests/

# 型チェック
poetry run mypy src/
```

### テストの実行

```bash
# 全テスト実行
poetry run pytest

# カバレッジ付きテスト
poetry run pytest --cov=src tests/

# 特定のテストファイルのみ実行
poetry run pytest tests/test_algorithms.py

# 詳細な出力
poetry run pytest -v
```

### 依存関係の管理

```bash
# 新しいパッケージの追加
poetry add <package-name>

# 開発用パッケージの追加
poetry add --group dev <package-name>

# パッケージの削除
poetry remove <package-name>

# 依存関係の更新
poetry update
```

## VSCode 推奨設定

`.vscode/settings.json` を作成して以下を追加：

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.path": "isort",
    "editor.formatOnSave": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

## トラブルシューティング

### Poetry が見つからない

```bash
# パスが通っているか確認
echo $PATH

# Poetry の場所を確認
which poetry
```

### 依存関係のインストールエラー

```bash
# キャッシュをクリア
poetry cache clear pypi --all

# 再インストール
poetry install --no-cache
```

### OR-Tools のインストールエラー

一部の環境では OR-Tools のインストールに問題が発生する場合があります：

```bash
# pip を最新版に更新
poetry run pip install --upgrade pip

# 個別にインストール
poetry run pip install ortools
```

## 環境変数

必要に応じて `.env` ファイルを作成：

```bash
# .env
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

## Docker を使用する場合（オプション）

```bash
# イメージのビルド
docker build -t job-allocation-demo .

# コンテナの実行
docker run -p 8501:8501 job-allocation-demo
```