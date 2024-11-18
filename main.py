import os
from typing import Any
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

class AutoNut(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # 메시지 내용을 읽기 위해 필요
        super().__init__(
            command_prefix="!",
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.session = None  # aiohttp 세션 관리용

    async def setup_hook(self):
        # 비동기 초기화 작업
        self.session = aiohttp.ClientSession()

        # 명령어 확장 로드
        await self.load_extension("cogs.bili_notify_set")
        await self.load_extension("cogs.bili_pre_rank")
        await self.load_extension("cogs.countdown")
        await self.load_extension("cogs.auto_trans")

        # 명령어 동기화
        await self.tree.sync()

    async def on_ready(self):
        # 봇 준비 완료 상태 처리
        print(f"[DEBUG] {self.user}로 로그인했습니다.")
        activity = discord.Activity(type=discord.ActivityType.watching, name="📺 YouTube @MayNut")  # 봇 활동 표시
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        # 에러 처리
        print(f"[ERROR] Error in {event_method}: {args}, {kwargs}")
        return await super().on_error(event_method, *args, **kwargs)

    async def on_command_error(self, context, exception) -> None:
        # 명령어 실행 중 발생한 에러 처리
        print(f"[ERROR] Command error: {context}, {exception}")
        return await super().on_command_error(context, exception)

    async def close(self):
        # 봇 종료 시 세션 닫기
        await super().close()
        if self.session:
            await self.session.close()

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")  # 봇 토큰

    bot = AutoNut()  # AutoNut 인스턴스 생성
    bot.run(TOKEN)  # 봇 실행