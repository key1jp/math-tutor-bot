# math-tutor-bot

中学受験をサポートする算数指導Discord Bot「ますお先生」

## 概要

小学生の中学受験算数学習をサポートするDiscord Botです。Google Gemini AIを活用し、画像付きの算数問題にも対応できる親しみやすい先生キャラクターとして動作します。

## 主な機能

- **テキスト質問対応**: 算数の問題や概念について質問可能
- **画像問題解析**: 手書きや印刷された算数問題の画像を解析
- **スレッド管理**: 質問ごとに自動でスレッドを作成し、会話履歴を保持
- **教育的指導**: 答えを直接教えるのではなく、考え方やヒントを提供
- **AWS Fargate Spot**: コスト効率的なクラウド運用

## 技術スタック

- **Python 3.11**
- **Discord.py**: Discord Bot API
- **Google Gemini AI**: テキスト・画像解析
- **PIL (Pillow)**: 画像処理
- **AWS Fargate Spot**: コンテナ実行環境
- **CloudFormation**: インフラ管理

## セットアップ

### 必要な環境変数

```bash
GEMINI_API_KEY=your_gemini_api_key
DISCORD_BOT_TOKEN=your_discord_bot_token
```

### ローカル実行

```bash
# 依存関係インストール
pip install -r requirements.txt

# Bot実行
python mathbot.py
```

### AWS デプロイ

```bash
# 初回デプロイ（環境変数設定込み）
./deploy.sh GEMINI_API_KEY DISCORD_BOT_TOKEN DISCORD_WEBHOOK_URL

# 更新デプロイ（既存の環境変数使用）
./deploy.sh
```

## 使用方法

1. Discord サーバーにBotを招待
2. `@ますお先生` でメンション
3. テキストまたは画像付きで算数の質問を送信
4. 自動作成されるスレッドで継続的な学習サポートを受ける