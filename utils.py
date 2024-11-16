import re
import deepl
import os
import discord
from datetime import datetime
import random
from dotenv import load_dotenv
from file_io import load_channel_setting

# 환경 변수 로드 및 DeepL API 설정
load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
translator = deepl.Translator(DEEPL_API_KEY)

# ------------------ 번역 관련 ------------------
# DeepL API를 사용하여 텍스트를 번역
# - text: 번역할 텍스트
# - target_lang: 번역 대상 언어 (기본값: 'KO')
async def translate_text_deepl(text, target_lang='KO'):
    try:
        result = translator.translate_text(text, target_lang=target_lang)
        return result.text
    except Exception as e:
        print(f"DeepL 오류: {e}")
        return text

# ------------------ 중국어 메시지 확인 ------------------
# 메시지가 중국어인지 확인
# - message_content: 메시지 내용
def is_message_chinese(message_content):
    chinese_numeric_regex = re.compile(r"[\u4E00-\u9FFF]")
    total_characters = len(message_content.replace(" ", ""))
    if total_characters == 0:
        return False
    chinese_numeric_count = len(chinese_numeric_regex.findall(message_content))
    return (chinese_numeric_count / total_characters) >= 0.6

# ------------------ 텍스트를 인용 형식으로 변환 ------------------
# 공유된 텍스트를 인용 형식으로 변환
# - text: 변환할 텍스트
def format_as_quote(text):
    # 텍스트를 줄바꿈(`\n`)을 기준으로 분리한 후, 각 줄 앞에 `>` 추가
    quoted_text = '\n'.join([f"> {line}" for line in text.splitlines()])
    return quoted_text

# ------------------ 임베드 메시지 생성 ------------------
# 디스코드 임베드 메시지 생성
# - post: 게시물 데이터
# - host_mid: 게시물 작성자의 host_mid
# - channel_id: 채널 ID
async def create_embed(post, host_mid, channel_id):
    embed = discord.Embed()

    embed.set_author(name=f"{post.get('author_name', host_mid)} (UID_{host_mid})", url=f"https://space.bilibili.com/{host_mid}")
    embed.set_footer(text="bilibili")
    embed.timestamp = datetime.fromisoformat(post['get_time'])

    channel_setting = await load_channel_setting()
    channel_translation = channel_setting[channel_id].get("translation", False)

    if post["type"] == "DYNAMIC_TYPE_AV":
        embed.title = f"**{await translate_text_deepl(post['title'], target_lang='KO') if channel_translation else post['title']}**"
        embed.url = f"https:{post['video_link']}"
        embed.set_thumbnail(url=post["cover"])
        embed.color = discord.Color.blue()

    elif post["type"] == "DYNAMIC_TYPE_DRAW":
        embed.description = await translate_text_deepl(post['text'], target_lang='KO') if channel_translation else post['text']
        embed.set_thumbnail(url=post["author_face"])
        embed.set_image(url=f"{post['image_link']}?cache_bust={random.randint(1,100)}") if post.get("image_link") else None
        embed.color = discord.Color.green()

    elif post["type"] == "DYNAMIC_TYPE_FORWARD":
        forward_text = await translate_text_deepl(post['forward_text'], target_lang='KO') if channel_translation else post['forward_text']    
        if post.get("original_type") == "DYNAMIC_TYPE_AV":
            embed.description = f"{forward_text}\n\n" \
                                f"`───── 공유한 동영상 ─────`\n> **{post.get('original_title')}**\nhttps:{post.get('original_video_link')}"
        else:
            formatted_text = format_as_quote(post["original_text"])
            embed.description = f"{forward_text}\n\n" \
                                f"`───── 공유한 게시물 ─────`\nhttps://www.bilibili.com/opus/{post['original_id']}\n> \n{formatted_text}"
        embed.set_thumbnail(url=post["author_face"])
        embed.color = discord.Color.purple()

    elif post["type"] == "DYNAMIC_TYPE_WORD":
        embed.description = await translate_text_deepl(post['text'], target_lang='KO') if channel_translation else post['text']
        embed.set_thumbnail(url=post["author_face"])
        embed.color = discord.Color.orange()

    elif post["type"] == "DYNAMIC_TYPE_ARTICLE":
        embed.title = f"**{await translate_text_deepl(post['title'], target_lang='KO') if channel_translation else post['title']}**"
        embed.description = await translate_text_deepl(post['text'], target_lang='KO') if channel_translation else post['text']
        embed.set_thumbnail(url=post["author_face"])
        embed.set_image(url=f"{post['image_link']}?cache_bust={random.randint(1,100)}") if post.get("image_link") else None
        embed.color = discord.Color.yellow()

    else:
        # 기타 타입의 게시물 설정
        embed.description = f"미리보기 미지원 타입 (타입: {post['type']})"
        embed.set_thumbnail(url=post["author_face"])
        embed.color = discord.Color.red()

    return embed

# ------------------ 메시지 전송 ------------------
# 지정된 디스코드 채널에 메시지를 전송
# - channel: 디스코드 채널 객체
# - post: 게시물 데이터
# - host_mid: 게시물 작성자의 host_mid
# - channel_id: 채널 ID
async def send_message(channel, post, host_mid, channel_id):
    embed = await create_embed(post, host_mid, channel_id)
    channel_setting = await load_channel_setting()    
    channel_mention = channel_setting[channel_id].get("mention", "")

    if post["type"] == "DYNAMIC_TYPE_AV":
        content=(
            (f"{channel_mention}\n" if channel_mention else "") +
            f"🔔 **{post['author_name']}** 님의 새로운 동영상이 도착했습니다!\n"
            f"<https:{post['video_link']}>"
        )
    elif post["type"] == "DYNAMIC_TYPE_FORWARD":
        content=(
            (f"{channel_mention}\n" if channel_mention else "") +
            f"🔔 **{post['author_name']}** 님이 {'동영상' if post.get('original_type') == 'DYNAMIC_TYPE_AV' else '게시물'}을 공유했습니다!\n"
            f"https://t.bilibili.com/{post['id']}"
        )
    elif post["type"] == "DYNAMIC_TYPE_ARTICLE":
        content=(
            (f"{channel_mention}\n" if channel_mention else "") +
            f"🔔 **{post['author_name']}** 님의 새로운 기사가 도착했습니다!\n"
            f"https://www.bilibili.com/opus/{post['id']}"
        )
    else:
        content=(
            (f"{channel_mention}\n" if channel_mention else "") +
            f"🔔 **{post['author_name']}** 님의 새로운 게시물이 도착했습니다!\n"
            f"https://www.bilibili.com/opus/{post['id']}"
        )

    try:
        await channel.send(content=content, embed=embed)
    except discord.Forbidden:
        print(f"[ERROR] Discord API: Forbidden - 봇이 채널 {channel_id}에 메시지를 보낼 권한이 없습니다.")
    except discord.HTTPException as e:
        print(f"[ERROR] Discord API: HTTPException - 채널 {channel_id}, 오류: {e}")
    except Exception as e:
        print(f"[ERROR] 메시지 전송 실패: 채널 {channel_id}, 오류: {type(e).__name__} - {e}")