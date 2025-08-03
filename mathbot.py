from discord import Client, Intents, Thread
import google.generativeai as genai
from os import getenv
import io
import logging
from PIL import Image

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('discord-bot')

# 環境変数からキーとトークンを取得
GEMINI_API_KEY = getenv('GEMINI_API_KEY')
DISCORD_BOT_TOKEN = getenv('DISCORD_BOT_TOKEN')

# --- 👨‍🏫 キャラクター設定 (算数の先生) ---
# 小学生の受験をサポートする、親しみやすい算数の先生として振る舞います。
def load_character_context():
    try:
        with open('character_context.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error("character_context.txt not found")
        return "算数の先生として丁寧に指導してください。"

CHARACTER_CONTEXT = load_character_context()

# ---------------------------------------------------------

# Gemini APIの設定
genai.configure(api_key=GEMINI_API_KEY)
# ✨ 画像対応のモデルに変更
model = genai.GenerativeModel('gemini-2.5-flash') 
# 画像処理用にgemini-2.5-proを使用
image_model = genai.GenerativeModel('gemini-2.5-pro')

# Discord Botの接続設定
intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f'{client.user} としてログインしました')
    logger.info(f'Bot ID: {client.user.id}')
    logger.info(f'接続サーバー数: {len(client.guilds)}')
    for guild in client.guilds:
        logger.info(f'  - {guild.name} (ID: {guild.id})')

@client.event
async def on_message(message):
    if message.author == client.user:
        logger.debug(f'message.author ={message.author}. return.')
        return

    if client.user.mentioned_in(message):
        logger.info("Bot mentioned")
        user_message = message.content.replace(f'<@!{client.user.id}>', '').strip()
        
        # スレッド内かどうかを判別
        is_in_thread = isinstance(message.channel, Thread)
        thread_info = f" (スレッド: {message.channel.name})" if is_in_thread else " (通常チャンネル)"
        
        sanitized_message = user_message.replace('\n', ' ').replace('\r', ' ')
        sanitized_username = message.author.display_name.replace('\n', ' ').replace('\r', ' ')
        logger.info(f'受付{thread_info}: {sanitized_message}, ユーザー: {sanitized_username}')

        # ✨ --- ここから画像処理のロジックを追加 ---
        response_text = ""
        target_channel = message.channel
        thread = None
        
        try:
            async with message.channel.typing():
                # 画像が添付されているかチェック
                if message.attachments:
                    # 最初の添付ファイルを取得
                    attachment = message.attachments[0]
                    # 画像ファイルかどうかの簡易チェック
                    if attachment.content_type.startswith('image/'):
                        logger.info("Image Found.")
                        # 画像データをダウンロードしてPILイメージに変換
                        image_bytes = await attachment.read()
                        img = Image.open(io.BytesIO(image_bytes))

                        # スレッド内かどうかで処理を分岐
                        if is_in_thread:
                            # スレッド内の場合：会話履歴を取得
                            history_messages = []
                            async for hist_msg in message.channel.history(limit=50, oldest_first=True):
                                if hist_msg.author == client.user:
                                    history_messages.append(f"先生: {hist_msg.content}")
                                elif hist_msg != message:  # 現在のメッセージは除外
                                    content = hist_msg.content.replace(f'<@!{client.user.id}>', '').strip()
                                    if content:
                                        history_messages.append(f"生徒: {content}")
                            
                            conversation_history = "\n".join(history_messages)
                            prompt_parts = [
                                CHARACTER_CONTEXT,
                                "\n\n---\n\n過去の会話履歴:\n" + conversation_history,
                                f"\n\n---\n\n{message.author.display_name} さんからの新しい質問です。画像とテキストをよく見て、これまでの会話を踏まえて先生として分かりやすく丁寧に応答してください。\n",
                                "テキスト: \"" + user_message + "\"",
                                img
                            ]
                            target_channel = message.channel
                        else:
                            # 通常チャンネルの場合：新しいスレッドを作成
                            thread_name = user_message[:50] + "..." if len(user_message) > 50 else user_message
                            if not thread_name.strip():
                                thread_name = "算数の質問（画像あり）"
                            thread = await message.create_thread(name=thread_name)
                            target_channel = thread
                            
                            prompt_parts = [
                                CHARACTER_CONTEXT,
                                f"\n\n---\n\n{message.author.display_name} さんからの質問です。画像とテキストをよく見て、先生として分かりやすく丁寧に応答してください。\n",
                                "テキスト: \"" + user_message + "\"",
                                img
                            ]
                        
                        response = await image_model.generate_content_async(prompt_parts)
                        response_text = response.text
                    else:
                        response_text = "ごめんね、これは画像ファイルではないみたいだ。画像を送ってくれるかな？"
                        if not is_in_thread:
                            thread_name = "ファイル形式エラー"
                            thread = await message.create_thread(name=thread_name)
                            target_channel = thread
                
                # 画像が添付されていない場合（テキストのみ）
                else:
                    logger.debug("添付ファイルなし")
                    if not user_message:
                        response_text = "こんにちは！算数の勉強で分からないことはあるかな？先生に何でも質問してね！"
                        if not is_in_thread:
                            thread_name = "挨拶"
                            thread = await message.create_thread(name=thread_name)
                            target_channel = thread
                    else:
                        # スレッド内かどうかで処理を分岐
                        if is_in_thread:
                            # スレッド内の場合：会話履歴を取得
                            history_messages = []
                            async for hist_msg in message.channel.history(limit=50, oldest_first=True):
                                if hist_msg.author == client.user:
                                    history_messages.append(f"先生: {hist_msg.content}")
                                elif hist_msg != message:  # 現在のメッセージは除外
                                    content = hist_msg.content.replace(f'<@!{client.user.id}>', '').strip()
                                    if content:
                                        history_messages.append(f"生徒: {content}")
                            
                            conversation_history = "\n".join(history_messages)
                            full_prompt = f"{CHARACTER_CONTEXT}\n\n---\n\n過去の会話履歴:\n{conversation_history}\n\n---\n\n{message.author.display_name} さんからの新しい質問: \"{user_message}\"\n\nこれまでの会話を踏まえて、先生として分かりやすく丁寧に応答してください。"
                            target_channel = message.channel
                        else:
                            # 通常チャンネルの場合：新しいスレッドを作成
                            thread_name = user_message[:50] + "..." if len(user_message) > 50 else user_message
                            if not thread_name.strip():
                                thread_name = "算数の質問"
                            thread = await message.create_thread(name=thread_name)
                            target_channel = thread
                            
                            full_prompt = f"{CHARACTER_CONTEXT}\n\n---\n\n{message.author.display_name} さんからの質問: \"{user_message}\"\n\n上記の先生として、分かりやすく丁寧に応答してください."
                        
                        response = await model.generate_content_async(full_prompt)
                        response_text = response.text
                
                # 適切なチャンネル（スレッドまたは元のチャンネル）に返信
                if response_text:
                    # レスポンスからメンションを除去
                    import re
                    cleaned_response = re.sub(r'<@!?\d+>', '', response_text).strip()
                    # 送信者にメンションして返信
                    mention_response = f"{message.author.mention} {cleaned_response}"
                    await target_channel.send(mention_response)

        except Exception as e:
            error_message = f"おっと、ますお先生体調が悪くなってしまった！逃げてるわけじゃないぞ！しばらく経ったらまた質問してくれるかな？\n`{e}`"
            
            # エラーメッセージも必ずスレッドで送信
            try:
                if is_in_thread:
                    await message.channel.send(error_message)
                else:
                    # 通常チャンネルの場合、必ずスレッドを作成してエラーメッセージを送信
                    if thread:
                        await thread.send(error_message)
                    else:
                        error_thread = await message.create_thread(name="エラー")
                        await error_thread.send(error_message)
            except Exception as thread_error:
                # スレッド作成に失敗した場合のフォールバック
                logger.error(f"スレッド作成エラー: {thread_error}")
                await message.channel.send(error_message)
            
            logger.error(f"エラー: {e}", exc_info=True)

# ボットを実行
client.run(DISCORD_BOT_TOKEN)