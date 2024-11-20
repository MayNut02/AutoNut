import json
import os
import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.utils import get
from datetime import datetime
from file_io import load_feed_data, save_feed_data

class NaverLounge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.target_lounge_name = 'Strinova'
        self.target_channel_id = 1305042440176275496  # 스트리노바KR > 한섭공지
        self.check_new_feeds.start()  # 10분마다 실행되는 작업 시작

    # API 호출 함수: 리스트 API
    def fetch_feed_list(self, params, headers):
        list_url = f"https://comm-api.game.naver.com/nng_main/v1/community/lounge/{self.target_lounge_name}/feed"
        response = requests.get(list_url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"리스트 API 호출 실패: {response.status_code}")

    # API 호출 함수: 상세 API
    def fetch_feed_detail(self, feed_id, headers):
        detail_url = f"https://comm-api.game.naver.com/nng_main/v1/community/lounge/{self.target_lounge_name}/feed/{feed_id}"
        response = requests.get(detail_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"상세 API 호출 실패: {response.status_code}")

    # HTML 콘텐츠 파싱
    def parse_html_content(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

    # Discord Embed 생성
    def create_embed(self, nickname, profile_image, title, createdDate, feed_id, text_content, rep_image_url):
        # 작성 시간 포맷 변환 (YYYYMMDDHHMMSS -> datetime 객체)
        try:
            timestamp = datetime.strptime(createdDate, "%Y%m%d%H%M%S")
        except ValueError:
            timestamp = None  # 변환 실패 시 None으로 설정

        embed = discord.Embed(
            title=title,
            url=f"https://game.naver.com/lounge/Strinova/board/detail/{feed_id}",
            description=text_content,
            color=discord.Color.green()
        )
        embed.set_author(name=nickname, url="https://game.naver.com/lounge/Strinova/home")
        embed.set_thumbnail(url=profile_image)
        embed.set_footer(text=f"Naver Game")
        if rep_image_url:
            embed.set_image(url=rep_image_url)
        # Timestamp 추가
        if timestamp:
            embed.timestamp = timestamp
        return embed

    # 새로운 데이터를 Discord로 전송
    async def send_new_feeds(self, channel, new_feeds, headers):
        # 채널 객체 가져오기
        channel = self.bot.get_channel(self.target_channel_id)
        if not channel:
            print(f"⚠️ 채널 ID {self.target_channel_id}를 찾을 수 없습니다.")
            return
        
        for feed in new_feeds:
            feed_id = feed["feedId"]
            feed_detail = self.fetch_feed_detail(feed_id, headers)
            loungeName = feed_detail.get("content", {}).get("lounge", {}).get("loungeName", "알 수 없음")
            nickname = feed_detail.get("content", {}).get("user", {}).get("nickname", "알 수 없음")
            profile_image = feed_detail.get("content", {}).get("user", {}).get("profileImageUrl", "")
            title = feed_detail.get("content", {}).get("feed", {}).get("title", "제목 없음")
            createdDate = feed_detail.get("content", {}).get("feed", {}).get("createdDate", "제목 없음")
            contents = feed_detail.get("content", {}).get("feed", {}).get("contents", "")
            rep_image_url = feed_detail.get("content", {}).get("feed", {}).get("repImageUrl", "")

            # HTML 콘텐츠 파싱
            text_content = self.parse_html_content(contents)
            # 200자로 자르기
            if len(text_content) > 200:
                text_content = text_content[:200] + "..."

            # Embed 생성 및 전송
            embed = self.create_embed(nickname, profile_image, title, createdDate, feed_id, text_content, rep_image_url)
            content=(
                f"@everyone\n🔔 **{loungeName} 라운지**에 새로운 공지가 올라왔습니다!\n"
                f"<https://game.naver.com/lounge/Strinova/board/detail/{feed_id}>"
            )
            await channel.send(content=content, embed=embed)

    @tasks.loop(minutes=10)
    async def check_new_feeds(self):
        params = {
            "boardId": 3,
            "buffFilteringYN": "N",
            "limit": 3,  # 최대 3개의 데이터를 가져옴
            "offset": 0,
            "order": "NEW"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        }

        try:
            feed_list = self.fetch_feed_list(params, headers)
            feeds = feed_list.get("content", {}).get("feeds", [])

            # 기존 데이터를 읽어 비교
            existing_feed_ids = await load_feed_data(self.target_lounge_name)
            # existing_feed_ids = set(existing_data.get("feed_ids", []))

            # 새로운 피드만 필터링
            new_feeds = [feed for feed in feeds if feed["feedId"] not in existing_feed_ids]

            if new_feeds:
                # Discord 채널 가져오기 (예시로 첫 번째 길드의 첫 번째 텍스트 채널 사용)
                guild = self.bot.guilds[0]
                channel = guild.text_channels[0]

                # 새로운 피드를 Discord로 전송
                await self.send_new_feeds(channel, new_feeds, headers)

                # JSON 데이터 갱신
                new_feed_ids = [feed["feedId"] for feed in new_feeds]
                existing_feed_ids.extend(new_feed_ids)
                await save_feed_data(self.target_lounge_name, existing_feed_ids)

        except Exception as e:
            print(f"[ERROR] 오류 발생 : {e}")

    @check_new_feeds.before_loop
    async def before_check_new_feeds(self):
        await self.bot.wait_until_ready()

# Cog 설정
async def setup(bot: commands.Bot):
    await bot.add_cog(NaverLounge(bot))
