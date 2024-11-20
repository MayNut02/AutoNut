# 파일 입출력 관련 함수
import json
import aiofiles
import os

DATA_DIR = 'host_data'  # 데이터 저장 디렉터리
WATCH_LIST_FILE = 'watch_list.json'  # 감시 목록 파일
CHANNEL_SETTING_FILE = 'channel_setting.json'  # 채널 설정 파일
PRE_RANK_FILE = 'pre_rank.json'  # 사전예약 랭킹 데이터 파일
LOUNGE_FEEDS_FILE = 'lounge_feedS.json'

# 비리비리 감시 목록 로드
async def load_watch_list():
    try:
        async with aiofiles.open(WATCH_LIST_FILE, 'r', encoding='utf-8') as file:
            watch_list = json.loads(await file.read())
        return watch_list.get("host_mids", [])
    except FileNotFoundError:
        return []

# 비리비리 감시 목록 저장
async def save_watch_list(host_mids):
    async with aiofiles.open(WATCH_LIST_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps({"host_mids": host_mids}, indent=4))

# 네이버 라운지 감시 목록 로드
async def load_feed_data(lounge):
    try:
        async with aiofiles.open(LOUNGE_FEEDS_FILE, 'r', encoding='utf-8') as file:
            watch_list = json.loads(await file.read())
        return watch_list.get(lounge, [])
    except FileNotFoundError:
        return []

# 네이버 라운지 감시 목록 저장
async def save_feed_data(lounge, feed_ids):
    async with aiofiles.open(LOUNGE_FEEDS_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps({lounge: feed_ids}, indent=4))

# 채널 설정 로드
async def load_channel_setting():
    try:
        async with aiofiles.open(CHANNEL_SETTING_FILE, 'r', encoding='utf-8') as file:
            content = await file.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}

# 채널 설정 저장
async def save_channel_setting(channel_setting):
    async with aiofiles.open(CHANNEL_SETTING_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(channel_setting, indent=4))

# 지정된 host_mid에 대한 JSON 파일을 생성
async def create_host_mid_file(host_mid):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{host_mid}.json")
    if not os.path.exists(file_path):
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps([]))

# host_mid에 해당하는 파일에서 author_name을 가져옴
async def get_author_name(host_mid):
    file_path = os.path.join(DATA_DIR, f"{host_mid}.json")
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            data = json.loads(await file.read())
        return data[0].get("author_name", host_mid) if data else host_mid
    except FileNotFoundError:
        print(f"[ERROR] {file_path} 파일이 없음")
        return None

# 사전예약 랭킹 데이터 파일 로드
async def get_pre_rank_file():
    try:
        async with aiofiles.open(PRE_RANK_FILE, 'r', encoding='utf-8') as file:
            return json.loads(await file.read())
    except FileNotFoundError:
        print("[ERROR] pre_rank.json 파일이 없음")
        return []
