import aiohttp
import asyncio
import json
import os
import aiofiles
from dotenv import load_dotenv
from datetime import datetime, timezone

# 환경 변수 로드
load_dotenv()

# API URL 및 헤더 설정
URL_TEMPLATE = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?offset=&host_mid={}"
URL_PRE_RANK_API = "https://le3-api.game.bilibili.com/pc/game/ranking/page_ranking_list?ranking_type=5&page_num={}&page_size=20"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": os.getenv("COOKIE")
    #"Cookie": f"buvid3={os.getenv('BUVID3')};"
}

WATCH_LIST_FILE = 'watch_list.json'    # 감시 대상 목록 파일
PRE_RANK_FILE = 'pre_rank.json'        # 사전예약 순위 데이터 파일
DATA_DIR = 'host_data'                 # 데이터 저장 디렉토리
UDS_PATH = "/tmp/monitor_signal.sock"  # UDS 경로
os.makedirs(DATA_DIR, exist_ok=True)   # 데이터 디렉토리 생성
file_lock = asyncio.Lock()             # 파일 동기화를 위한 Lock

# watch_list.json에서 host_mid 목록을 로드
async def load_watch_list():
    try:
        async with aiofiles.open(WATCH_LIST_FILE, 'r', encoding='utf-8') as file:
            watch_list = json.loads(await file.read())
        return watch_list.get("host_mids", [])
    except FileNotFoundError:
        return []

# 게시물 데이터를 타입별로 추출하여 반환
def extract_data_by_type(post):
    post_type = post.get("type", "UNKNOWN")
    base_data = {
        "id": post.get("id_str"),
        "type": post_type,
        "author_name": post.get("modules", {}).get("module_author", {}).get("name", ""),
        "author_face": post.get("modules", {}).get("module_author", {}).get("face", ""),
        "get_time": datetime.now(timezone.utc).isoformat(),
    }
    
    # 영상 게시물 데이터
    if post_type == "DYNAMIC_TYPE_AV":
        major = post.get("modules", {}).get("module_dynamic", {}).get("major", {})
        return {
            **base_data,
            "video_link": major.get("archive", {}).get("jump_url", ""),
            "title": major.get("archive", {}).get("title", ""),
            "description": major.get("archive", {}).get("desc", ""),
            "cover": major.get("archive", {}).get("cover", "")
        }
    # 이미지 게시물 데이터
    elif post_type == "DYNAMIC_TYPE_DRAW":
        major = post.get("modules", {}).get("module_dynamic", {}).get("major", {})
        images = major.get("draw", {}).get("items", [])
        return {
            **base_data,
            "text": post.get("modules", {}).get("module_dynamic", {}).get("desc", {}).get("text", ""),
            "image_link": images[0].get("src") if images else None  # 최상단 이미지 링크만 저장
        }
    # 공유 게시물 데이터
    elif post_type == "DYNAMIC_TYPE_FORWARD":
        orig = post.get("orig", {})
        original_type = orig.get("type", "")
        forward_data = {
            **base_data,
            "forward_text": post.get("modules", {}).get("module_dynamic", {}).get("desc", {}).get("text", ""),
            "original_id": orig.get("id_str", ""),
            "original_type": original_type,
        }
        # 원본이 비디오인 경우 타이틀과 링크 저장
        if original_type == "DYNAMIC_TYPE_AV":
            major = orig.get("modules", {}).get("module_dynamic", {}).get("major", {})
            forward_data.update({
                "original_video_link": major.get("archive", {}).get("jump_url", ""),
                "original_title": major.get("archive", {}).get("title", ""),
            })
        # 원본이 다른 타입일 경우 텍스트 저장
        else:
            forward_data.update({
                "original_text": orig.get("modules", {}).get("module_dynamic", {}).get("desc", {}).get("text", "")
            })
        return forward_data
    # 텍스트 게시물 데이터
    elif post_type == "DYNAMIC_TYPE_WORD":
        return {
            **base_data,
            "text": post.get("modules", {}).get("module_dynamic", {}).get("desc", {}).get("text", "")
        }
    # 기사 게시물 데이터
    elif post_type == "DYNAMIC_TYPE_ARTICLE":
        major = post.get("modules", {}).get("module_dynamic", {}).get("major", {})
        images = major.get("article", {}).get("covers", [])
        return {
            **base_data,
            "title": post.get("modules", {}).get("module_dynamic", {}).get("major", {}).get("article", {}).get("title", ""),
            "text": post.get("modules", {}).get("module_dynamic", {}).get("major", {}).get("article", {}).get("desc", ""),
            "image_link": images[0] if images else None  # 최상단 이미지 링크만 저장
        }
    # 기타 타입
    else:
        return base_data

# 특정 host_mid에 대한 데이터를 API로부터 호출
async def fetch_data(host_mid):
    url = URL_TEMPLATE.format(host_mid)
    timeout = aiohttp.ClientTimeout(total=10)  # 전체 요청 타임아웃 10초 설정
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                data = await response.json()
                items = data.get("data", {}).get("items", [])[4::-1]
                return [extract_data_by_type(item) for item in items]
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"[ERROR] API 요청 오류: {e} - host_mid {host_mid} 5분 후 재시도")
            await asyncio.sleep(300)           # 오류 발생 시 5분 대기
            return await fetch_data(host_mid)  # 이후 재귀 호출로 재시도

# 데이터를 JSON 파일로 저장
async def save_json(file_path, data):
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(data, indent=4, ensure_ascii=False))

# 특정 host_mid의 새로운 게시물을 확인하고 저장
async def check_new_posts(host_mid):
    file_path = os.path.join(DATA_DIR, f"{host_mid}.json")
    try:
        new_data = await fetch_data(host_mid)
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                existing_data = json.loads(await file.read())
                existing_ids = {post["id"] for post in existing_data}
        else:
            existing_data = []
            existing_ids = set()

        updated_posts = []

        for post in new_data:
            if post["id"] not in existing_ids:
                existing_data.append(post)
                updated_posts.append(post["id"])

        if updated_posts:
            await save_json(file_path, existing_data)
            for post_id in updated_posts:
                await send_signal_to_bot(host_mid, post_id)

    except Exception as e:
        print(f"[ERROR] {host_mid} 데이터 처리 오류: {e}")

# UDS를 통해 Discord 봇에 업데이트 신호를 전송
async def send_signal_to_bot(host_mid, post_id):
    try:
        if os.path.exists(UDS_PATH):
            reader, writer = await asyncio.open_unix_connection(UDS_PATH)
            try:
                message = f'update:{host_mid}:{post_id}'
                writer.write(message.encode())
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
        else:
            print("[ERROR] UDS_PATH가 존재하지 않습니다.")
    except Exception as e:
        print(f"[ERROR] UDS 통신 오류: {e}")

# 사전예약 순위 데이터를 API에서 가져와 JSON 파일로 저장
async def pre_rank_data():
    new_pre_rank_data = []
    for i in range(1, 4):
        url = URL_PRE_RANK_API.format(i)
        timeout = aiohttp.ClientTimeout(total=10)  # 전체 요청 타임아웃 10초 설정
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url, headers=HEADERS) as response:
                    data = await response.json()

                    # "code" 값이 0이 아닌 경우 처리
                    if data.get("code") != 0:
                        print("[ERROR] COOKIE - SESSDATA가 만료되었습니다.")
                        return  

                    base_data = data.get("data", {}).get("order_list", [])[:]
                    for item in base_data:
                        items = {
                            "title": item.get("title", ""),
                            "game_detail_link": item.get("game_detail_link", ""),
                            "icon": item.get("icon", ""),
                            "game_desc": item.get("game_desc", "")[:60],
                            "category": item.get("category", {}).get("name",""),
                            "tag_names": item.get("tag_names", [])[:],
                            #"developer_name": item.get("developer_name", ""),
                            #"video_cover_image": item.get("video_cover_image", "")
                        }
                        new_pre_rank_data.append(items)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[ERROR] URL_PRE_RANK_API 요청 오류: {e} - 10분 후 재시도")
                await asyncio.sleep(600)      # 오류 발생 시 10분 대기
                return await pre_rank_data()  # 이후 재귀 호출로 재시도
            
    async with aiofiles.open(PRE_RANK_FILE, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(new_pre_rank_data, indent=4, ensure_ascii=False))

# 주기적으로 새로운 게시물을 확인
async def new_post():
    while True:
        try:
            host_mids = await load_watch_list()
            # 모든 host_mid에 대한 추적 작업을 비동기적으로 실행
            tasks = [check_new_posts(host_mid) for host_mid in host_mids]
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"[ERROR] new_post Error: {e}")
        await asyncio.sleep(60)  # 60초마다 실행

# 1시간마다 사전예약 순위를 업데이트
async def pre_reservation_rank():
    while True:
        try:
            await pre_rank_data()
        except Exception as e:
            print(f"[ERROR] pre_reservation_rank Error: {e}")
        await asyncio.sleep(3600)   # 1시간

# 메인 실행 함수
async def main():
    print("[DEBUG] 프로그램 시작")
    await asyncio.gather(new_post(), pre_reservation_rank())

if __name__ == "__main__":
    asyncio.run(main())
