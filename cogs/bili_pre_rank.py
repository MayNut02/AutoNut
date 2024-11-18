# 사전예약순위 명령어 처리
import discord
from discord import app_commands
from discord.ext import commands
from file_io import get_pre_rank_file

# 비리비리 사전예약 게임 순위를 페이지 형식으로 출력하는 View
class BiliPreRankView(discord.ui.View):
    def __init__(self, pre_rank, embeds_per_page=5):
        super().__init__()
        self.pre_rank = pre_rank
        self.current_page = 0
        self.embeds_per_page = embeds_per_page
        self.update_buttons()

    # 페이지 상태에 따라 이전/다음 버튼을 동적으로 업데이트
    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousPageButton())
        if (self.current_page + 1) * self.embeds_per_page < len(self.pre_rank):
            self.add_item(NextPageButton())

    # 현재 페이지의 데이터를 기반으로 Embed 리스트 생성
    def generate_embeds(self):
        embeds = []
        start = self.current_page * self.embeds_per_page
        end = start + self.embeds_per_page
        n = start + 1
        for game in self.pre_rank[start:end]:
            game_tag = " ".join([f"`#{tag}`" for tag in game.get('tag_names', [])])
            description = f"`#{game.get('category', '')}` {game_tag}"
            embed = discord.Embed(
                title=game.get('title', ''),
                url=f"{game.get('game_detail_link', '')}",
                description=description,
            )
            colors = {
                1: discord.Color.gold(),
                2: discord.Color.greyple(),
                3: discord.Color.dark_gold(),
            }
            embed.color = colors.get(n, discord.Color.blue())
            icon_url = f"https:{game.get('icon', '')}"
            if icon_url.startswith("https://"):
                embed.set_thumbnail(url=icon_url)
            embed.set_author(name=f"{n}")
            embeds.append(embed)
            n += 1
        return embeds

# 사전예약 순위 이전 페이지 버튼
class PreviousPageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="⬅️ 이전 페이지", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if isinstance(view, BiliPreRankView):
            view.current_page -= 1
            view.update_buttons()
            embeds = view.generate_embeds()
            await interaction.response.edit_message(embeds=embeds, view=view)

# 사전예약 순위 다음 페이지 버튼
class NextPageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="다음 페이지 ➡️", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if isinstance(view, BiliPreRankView):
            view.current_page += 1
            view.update_buttons()
            embeds = view.generate_embeds()
            await interaction.response.edit_message(embeds=embeds, view=view)

# 사전예약 순위 Cog 정의
class PreRank(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="사전예약순위")
    async def pre_rank(self, interaction: discord.Interaction):
        """비리비리 사전예약 게임 순위를 표시합니다."""
        try:
            await interaction.response.defer(ephemeral=True)  # 비공개 응답 처리
            pre_rank = await get_pre_rank_file()  # 사전예약 데이터 가져오기
            view = BiliPreRankView(pre_rank)
            embeds = view.generate_embeds()
            await interaction.followup.send(embeds=embeds, view=view)
        except Exception as e:
            await interaction.followup.send(
                content=f"⚠️ 순위 데이터를 불러오는 중 오류가 발생했습니다: {e}",
                ephemeral=True,
            )

# Cog을 봇에 추가
async def setup(bot: commands.Bot):
    await bot.add_cog(PreRank(bot))
