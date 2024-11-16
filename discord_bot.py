import discord
import os
import json
import aiofiles
import asyncio
from discord import app_commands
from dotenv import load_dotenv
from commands import setup_commands
from file_io import load_channel_setting
from utils import send_message, translate_text_deepl, is_message_chinese

# 환경 변수 로드
load_dotenv()

# Discord 봇 토큰 및 UDS 파일 경로 설정
TOKEN = os.getenv("DISCORD_TOKEN")
UDS_PATH = "/tmp/monitor_signal.sock"

# Discord 봇 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ------------------ UDS 파일 삭제 ------------------
# 기존 UDS 파일이 있을 경우 삭제
if os.path.exists(UDS_PATH):
    try:
        os.remove(UDS_PATH)
        print(f"[DEBUG] 기존 소켓 파일 {UDS_PATH} 삭제 완료")
    except Exception as e:
        print(f"[ERROR] 기존 소켓 파일 {UDS_PATH} 삭제 중 오류 발생: {e}")

# ------------------ UDS 모니터링 ------------------
# UDS를 통해 외부 신호를 모니터링하고 처리
async def monitor_signal():
    try:
        print("[DEBUG] monitor_signal() 시작 중...")
        server = await asyncio.start_unix_server(handle_signal, path=UDS_PATH)
        async with server:
            print("UDS 서버가 시작되었습니다. 신호를 기다리고 있습니다...")
            await server.serve_forever()
    except Exception as e:
        print(f"[ERROR] monitor_signal() 실행 중 오류 발생: {e}")

# UDS를 통해 수신된 신호를 처리
# - reader: 데이터를 읽는 스트림
# - writer: 데이터를 쓰는 스트림
async def handle_signal(reader, writer):
    try:
        data = await reader.read(100)
        message = data.decode()
        if message.startswith('update:'):
            _, host_mid, post_id = message.split(':')
            await check_discord_channel(host_mid, post_id)
    except Exception as e:
        print(f"[ERROR] 신호 처리 중 오류 발생: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

# ------------------ Discord 채널 메시지 처리 ------------------
# host_mid가 등록되어 있는 디스코드 채널에 메시지를 전송
# - host_mid: 대상 유저 ID
# - post_id: 게시물 ID
async def check_discord_channel(host_mid, post_id):
    await client.wait_until_ready()
    try:
        channel_setting = await load_channel_setting()
        channels = [
            channel_id
            for channel_id, settings in channel_setting.items()
            if settings.get("host_mid") == host_mid
        ]

        if channels:
            file_path = os.path.join('host_data', f"{host_mid}.json")
            if not os.path.exists(file_path):
                print(f"[ERROR] {file_path} 파일이 존재하지 않습니다.")
                return

            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                posts = json.loads(await file.read())
                post = next((item for item in posts if item["id"] == post_id), None)
                if not post:
                    print(f"[ERROR] {post_id}에 해당하는 게시물을 찾을 수 없습니다.")
                    return

                for channel_id in channels:
                    channel = client.get_channel(int(channel_id))
                    if not channel:
                        print(f"[ERROR] 유효하지 않은 채널 ID {channel_id}")
                        continue
                    try:
                        await send_message(channel, post, host_mid, channel_id)
                    except Exception as e:
                        print(f"[ERROR] send_message 호출 중 예외 발생: {type(e).__name__} - {e}")

    except Exception as e:
        print(f"[ERROR] {host_mid}의 채널 메시지 전송 중 오류 발생: {e}")

# ------------------ Discord 봇 이벤트 ------------------
# 디스코드 봇이 준비되었을 때 실행됨
@client.event
async def on_ready():
    await tree.sync()
    print(f"{client.user}로 로그인했습니다.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="📺 YouTube @MayNut"))

# 메시지 이벤트 처리
# - 채팅창에서 중국어 메시지 감지 시 자동으로 번역
@client.event
async def on_message(message):
    if message.author.bot:
        return  # 봇 메시지는 무시
    
    if is_message_chinese(message.content):  # 중국어 메시지 감지
        translated_text = await translate_text_deepl(message.content)
        response = f"**`중국어 자동 번역됨`**\n{translated_text}"
        await message.channel.send(response)

# ------------------ 봇 실행 ------------------
# Discord 봇을 실행
def run_bot():
    async def start_bot():
        asyncio.create_task(monitor_signal())   # UDS 모니터링 시작
        setup_commands(tree)        # 명령어 등록
        await client.start(TOKEN)   # Discord 봇 시작

    asyncio.run(start_bot())  # 비동기 이벤트 루프 실행