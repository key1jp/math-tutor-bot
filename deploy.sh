#!/bin/bash

# 引数チェック
if [ $# -ne 0 ] && [ $# -ne 3 ]; then
    echo "使用方法: $0 [GEMINI_API_KEY] [DISCORD_BOT_TOKEN] [DISCORD_WEBHOOK_URL]"
    echo "引数なし: 既存のSSMパラメータを使用"
    echo "引数あり: 新しい値でSSMパラメータを作成/更新"
    exit 1
fi

if [ $# -eq 3 ]; then
    GEMINI_API_KEY=$1
    DISCORD_BOT_TOKEN=$2
    DISCORD_WEBHOOK_URL=$3
    UPDATE_PARAMS=true
else
    UPDATE_PARAMS=false
fi

# 設定
AWS_REGION="ap-northeast-1"
ECR_REPOSITORY="discord-bot"
STACK_NAME="discord-bot-fargate-v2"

echo "ECRリポジトリ作成中..."
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || true

echo "ECRログイン中..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

echo "Dockerイメージビルド中..."
docker build --platform linux/arm64 -t $ECR_REPOSITORY .

echo "イメージタグ付け中..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$TIMESTAMP"
docker tag $ECR_REPOSITORY:latest $IMAGE_URI

echo "ECRにプッシュ中..."
docker push $IMAGE_URI

if [ "$UPDATE_PARAMS" = true ]; then
    echo "SSMパラメータ作成中..."
    aws ssm put-parameter \
        --name "/discord-bot/gemini-api-key" \
        --value "$GEMINI_API_KEY" \
        --type "SecureString" \
        --overwrite \
        --region $AWS_REGION

    aws ssm put-parameter \
        --name "/discord-bot/discord-bot-token" \
        --value "$DISCORD_BOT_TOKEN" \
        --type "SecureString" \
        --overwrite \
        --region $AWS_REGION

    aws ssm put-parameter \
        --name "/discord-bot/webhook-url" \
        --value "$DISCORD_WEBHOOK_URL" \
        --type "SecureString" \
        --overwrite \
        --region $AWS_REGION
else
    echo "既存のSSMパラメータを確認中..."
    aws ssm get-parameter --name "/discord-bot/gemini-api-key" --region $AWS_REGION > /dev/null
    aws ssm get-parameter --name "/discord-bot/discord-bot-token" --region $AWS_REGION > /dev/null
    aws ssm get-parameter --name "/discord-bot/webhook-url" --region $AWS_REGION > /dev/null
    echo "SSMパラメータが存在することを確認しました"
fi

echo "CloudFormationスタックデプロイ中..."
aws cloudformation deploy \
    --template-file fargate-spot-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        ImageUri="$IMAGE_URI" \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION

echo "デプロイ完了！"