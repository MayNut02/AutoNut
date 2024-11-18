import discord
from discord import app_commands
from discord.ext import commands
from file_io import load_channel_setting, save_channel_setting
from utils import translate_text_deepl, is_not_korean

class AutoTranslate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_settings = {}  # 채널별 설정 캐싱
        self.bot.loop.create_task(self.load_auto_trans_settings())  # 초기화 시 설정 로드

    # 초기 로드: 파일에서 설정 데이터를 캐싱
    async def load_auto_trans_settings(self):
        self.channel_settings = await load_channel_setting()

    # 설정 데이터를 파일에 저장
    async def save_auto_trans_settings(self):
        await save_channel_setting(self.channel_settings)

    # 메시지 이벤트 처리: 한글 외 메시지 자동 번역
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return  # 봇 메시지는 무시

        channel_id = str(message.channel.id)
        if channel_id not in self.channel_settings:
            # 캐싱 데이터에 기본값 추가
            self.channel_settings[channel_id] = {
                "host_mid": "",
                "mention": "",
                "translation": False,
                "auto_translate": False
            }

        if self.channel_settings[channel_id].get('auto_translate', False):
            # 한국어 메시지 감지
            if is_not_korean(message.content):
                permissions = message.channel.permissions_for(message.guild.me)
                if not permissions.send_messages:
                    return

                # 번역 처리
                translated_text = await translate_text_deepl(message.content)
                response = f"**`자동 번역됨`**\n{translated_text}"
                await message.channel.send(response)

    # 채널별 자동번역 설정 명령어
    @app_commands.command(name="자동번역설정")
    async def auto_translate_setting(self, interaction: discord.Interaction):
        """현재 채널의 자동번역 기능을 설정합니다."""
        channel_id = str(interaction.channel.id)

        # 캐싱 데이터에 기본값 추가 (없을 경우)
        if channel_id not in self.channel_settings:
            self.channel_settings[channel_id] = {
                "host_mid": "",
                "mention": "",
                "translation": False,
                "auto_translate": False
            }

        # auto_translate 값을 토글
        self.channel_settings[channel_id]["auto_translate"] = not self.channel_settings[channel_id]["auto_translate"]

        # 변경 사항 파일에 저장
        await self.save_auto_trans_settings()

        # Embed 생성
        embed = self.create_autotrans_setting_embed(
            interaction.guild, interaction.channel, self.channel_settings
        )
        await interaction.response.send_message(
            embed=embed,
            view=self.ViewAutoTransSetting(self.channel_settings, interaction.channel),
            ephemeral=True
        )

    # 메인 Embed 생성 함수
    def create_autotrans_setting_embed(self, guild, channel, channel_setting):
        autotrans_setting = channel_setting.get(str(channel.id), {}).get('auto_translate', False)
        return discord.Embed(
            title="자동번역 설정",
            description=(
                f"📢 **안내**\n"
                f"- 현재 채널의 자동번역 상태를 설정할 수 있습니다.\n\n"
                f"📌 **현재 채널**\n"
                f"- {guild.name} > {channel.name}\n\n"
                f"⚒️ **현재 채널 설정**\n"
                f"- 자동번역 : **{'ON' if autotrans_setting else 'OFF'}**"
            ),
            color=discord.Color.blue()
        )

    class ViewBackButton(discord.ui.View):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent

        @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = self.parent.create_autotrans_setting_embed(
                interaction.guild, interaction.channel, self.parent.channel_settings
            )
            await interaction.response.edit_message(
                embed=embed,
                view=self.parent.ViewAutoTransSetting(self.parent.channel_settings, interaction.channel)
            )

    class ViewAutoTransSetting(discord.ui.View):
        def __init__(self, channel_setting, channel):
            super().__init__()
            self.channel = channel  # 채널 정보 추가
            self.channel_setting = channel_setting
            self.update_button_label()

        def update_button_label(self):
            # 채널 ID가 포함된 설정 확인
            channel_id = str(self.channel.id)
            if self.channel_setting.get(channel_id, {}).get('auto_translate', False):
                self.children[0].label = "끄기"
                self.children[0].emoji = "⛔"
            else:
                self.children[0].label = "켜기"
                self.children[0].emoji = "✅"

        @discord.ui.button(emoji="✅", label="켜기", style=discord.ButtonStyle.green, row=0)
        async def toggle_autotranslate(self, interaction: discord.Interaction, button: discord.ui.Button):
            channel_id = str(interaction.channel.id)
            auto_translate = self.channel_setting.get(channel_id, {}).get('auto_translate', False)

            # 설정 토글
            self.channel_setting[channel_id]["auto_translate"] = not auto_translate
            await self.parent.save_auto_trans_settings()

            # Embed 업데이트
            new_embed = discord.Embed(
                title=f"🚀 자동번역을 {'종료' if auto_translate else '시작'}합니다!",
                description=f"현재 채널의 자동번역 설정이 **{'ON' if not auto_translate else 'OFF'}** 으로 변경되었습니다.",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=new_embed, view=self.parent.ViewBackButton(self.parent))

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoTranslate(bot))
