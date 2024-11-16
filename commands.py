import discord
from views import ViewBiliNotify, BiliPreRankView
from file_io import load_channel_setting, save_channel_setting, get_author_name, get_pre_rank_file

# ------------------ /알림설정 명령어 ------------------
# 알림설정 명령어 처리 함수
# - 채널에 비리비리 UID 등록, 알림 설정, 번역 설정 등을 관리
async def set_bili_notify(interaction: discord.Interaction):
    # 관리자 권한 확인
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⚠️ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return

    # 봇의 채널 메시지 전송 권한 확인
    channel = interaction.channel
    permissions = channel.permissions_for(interaction.guild.me)
    if not permissions.send_messages:
        await interaction.response.send_message("⚠️ 현재 채널에 메시지 전송 권한이 없습니다.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    channel_setting = await load_channel_setting()

    # 채널 설정에 현재 채널 ID가 없는 경우 기본값 추가
    if channel_id not in channel_setting:
        channel_setting[channel_id] = {
            "host_mid": "",       # UID 기본값
            "mention": "",        # 멘션 기본값
            "translation": False  # 번역 설정 기본값
        }
        await save_channel_setting(channel_setting)
        channel_setting = await load_channel_setting()

    # 채널 설정 정보 가져오기
    host_mid = channel_setting.get(channel_id, {}).get("host_mid", None)
    author_name = await get_author_name(host_mid) if host_mid else None
    channel_mention = channel_setting.get(channel_id, {}).get('mention', None)
    channel_translation = 'ON' if channel_setting.get(channel_id, {}).get('translation', None) else 'OFF'

    # 알림 설정 메뉴 Embed 메시지 생성
    embed = discord.Embed(
        title="알림설정",
        description=(
            f"📢 **안내**\n"
            f"- 비리비리 UID를 등록하면 새로운 게시물이 올라올 때 현재 채널에서 알림을 받을 수 있습니다.\n\n"
            f"📌 **현재 채널**\n"
            f"- {interaction.guild.name} > {interaction.channel.name}\n\n"
            f"⚒️ **현재 채널 설정**\n"
            f"- 등록된 계정 : **{f'[{author_name}](https://space.bilibili.com/{host_mid})' if host_mid else '없음'}**\n"
            f"- 멘션 설정 : **{channel_mention if channel_mention else '없음'}**\n"
            f"- 번역 설정 : **{channel_translation}**"
        ),
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=ViewBiliNotify(host_mid), ephemeral=True)

# ------------------ /카운트다운 명령어 ------------------
# 카운트다운 명령어 처리 함수
# - 스트리노바 출시 일정에 대한 카운트다운을 출력
# - 오픈 이후엔 현재 동접자를 확인하는 기능으로 수정
async def strinova_countdown(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**사전 다운로드\n<t:1731974400:R>** (<t:1731974400:F>)\n"
        "**서버 오픈\n<t:1732233600:R>** (<t:1732233600:F>)"
    )

# ------------------ /사전예약순위 명령어 ------------------
# 사전예약순위 명령어 처리 함수
# - 비리비리 사전예약 게임 순위를 출력
async def bili_pre_rank(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    pre_rank = await get_pre_rank_file()
    view = BiliPreRankView(pre_rank)
    embeds = view.generate_embeds()
    await interaction.followup.send(embeds=embeds, view=view)
    
# ------------------ 명령어 등록 ------------------
# 명령어를 디스코드 봇에 등록
# - tree: Discord 명령어 트리
def setup_commands(tree):
    tree.command(name="알림설정", description="현재 채널의 bilibili 알림 설정을 변경할 수 있습니다.")(set_bili_notify)
    tree.command(name="카운트다운", description="스트리노바 11월 22일 오전 9시 정식 출시!")(strinova_countdown)
    tree.command(name="사전예약순위", description="비리비리 사전예약 게임 순위")(bili_pre_rank)