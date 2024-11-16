import json
import aiofiles
import os

DATA_DIR = 'host_data'
WATCH_LIST_FILE = 'watch_list.json'
IDS_FILE = 'ids.json'
CHANNEL_SETTING_FILE = 'channel_setting.json'

# watch_list.json에서 host_mid 목록 로드
async def load_watch_list():
    try:
        async with aiofiles.open(WATCH_LIST_FILE, 'r', encoding='utf-8') as file:
            watch_list = json.loads(await file.read())
        return watch_list.get("host_mids", [])
    except FileNotFoundError:
        return []

# watch_list.json에 host_mid 목록 저장
async def save_watch_list(host_mids):
    async with aiofiles.open(WATCH_LIST_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps({"host_mids": host_mids}, indent=4))

# 채널 세팅 파일 로드
async def load_channel_setting():
    try:
        async with aiofiles.open(CHANNEL_SETTING_FILE, 'r', encoding='utf-8') as file:
            content = await file.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}

# 채널 세팅 파일 저장
async def save_channel_setting(channel_setting):
    async with aiofiles.open(CHANNEL_SETTING_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(channel_setting, indent=4))

# IDs 파일 로드
async def load_ids():
    try:
        async with aiofiles.open(IDS_FILE, 'r', encoding='utf-8') as file:
            content = await file.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}

# IDs 파일 저장
async def save_ids(ids_data):
    async with aiofiles.open(IDS_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(ids_data, indent=4))

# 지정된 host_mid.json 파일을 생성
async def create_host_mid_file(host_mid):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{host_mid}.json")
    if not os.path.exists(file_path):
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps([]))

# 비동기적으로 author_name을 가져오는 함수
async def get_author_name(host_mid):
    file_path = os.path.join(DATA_DIR, f"{host_mid}.json")
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            data = json.loads(await file.read())
            if data:
                author_name = data[0].get("author_name", host_mid)
            else:
                author_name = host_mid
        return author_name
    except FileNotFoundError:
        print(f"{file_path} 파일이 없음")

# 사전예약 랭킹 데이터 불러오기
async def get_pre_rank_file():
    try:
        async with aiofiles.open('pre_rank.json', 'r', encoding='utf-8') as file:
            return json.loads(await file.read())
    except FileNotFoundError:
        print("pre_rnak.json 파일이 없음")