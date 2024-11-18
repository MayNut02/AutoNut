# 카운트다운 명령어 처리
import discord
from discord import app_commands
from discord.ext import commands

class Countdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="카운트다운")
    async def countdown(self, interaction: discord.Interaction):
        """스트리노바 11월 22일 오전 9시 정식 출시!"""

        # 봇의 채널 메시지 전송 권한 확인
        channel = interaction.channel
        permissions = channel.permissions_for(interaction.guild.me)
        if not permissions.send_messages:
            await interaction.response.send_message("⚠️ 현재 채널에 메시지 전송 권한이 없습니다.", ephemeral=True)
            return
        
        try:
            await interaction.response.send_message(
                "**사전 다운로드\n<t:1731974400:R>** (<t:1731974400:F>)\n"
                "**서버 오픈\n<t:1732233600:R>** (<t:1732233600:F>)"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ 오류 발생: {e}",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Countdown(bot))
