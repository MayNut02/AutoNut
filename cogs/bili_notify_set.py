# 알림설정 명령어 처리
import discord
import os
import json
import aiofiles
import asyncio
import random
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select
from file_io import load_channel_setting, save_channel_setting, load_watch_list, save_watch_list, create_host_mid_file, get_author_name
from utils import translate_text_deepl, format_as_quote

UDS_PATH = "/tmp/monitor_signal.sock"

# 비리비리 알림 메시지 임베드 생성
async def create_bili_embed(post, host_mid, channel_id, channel_setting):
    embed = discord.Embed()
    embed.set_author(name=f"{post.get('author_name', host_mid)} (UID_{host_mid})", url=f"https://space.bilibili.com/{host_mid}")
    embed.set_footer(text="bilibili")
    embed.timestamp = datetime.fromisoformat(post['get_time'])
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
        forward_text = await translate_text_deepl(post['forward_text'], target_lang='KO') if channel_translation else post.get('forward_text')    
        if post.get("original_type") == "DYNAMIC_TYPE_AV":
            embed.description = f"{forward_text}\n\n" \
                                f"`───── 공유한 동영상 ─────`\n> **{post.get('original_title')}**\n> https:{post.get('original_video_link')}"
        else:
            formatted_text = format_as_quote(post.get('original_text', ''))
            embed.description = f"{forward_text}\n\n" \
                                f"`───── 공유한 게시물 ─────`\nhttps://www.bilibili.com/opus/{post.get('original_id')}\n\n> {formatted_text}"
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

# 비리비리 알림 메시지 전송
async def send_notice_message(channel, post, host_mid, channel_id, channel_setting):
    embed = await create_bili_embed(post, host_mid, channel_id, channel_setting)
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
    except discord.NotFound:
        print(f"[ERROR] Discord API: NotFound - 채널 {channel_id}이 존재하지 않습니다.")
    except discord.Forbidden:
        print(f"[ERROR] Discord API: Forbidden - 봇이 채널 {channel_id}에 메시지를 보낼 권한이 없습니다.")
    except discord.HTTPException as e:
        print(f"[ERROR] Discord API: HTTPException - 채널 {channel_id}, 오류: {e}")
    except Exception as e:
        print(f"[ERROR] 메시지 전송 실패: 채널 {channel_id}, 오류: {type(e).__name__} - {e}")

# 메인 Embed 생성 함수
def create_notify_embed(guild, channel, host_mid, author_name, channel_mention, channel_translation):
    return discord.Embed(
        title="비리비리 알림설정",
        description=(
            f"📢 **안내**\n"
            f"- 비리비리 UID를 등록하면 새로운 게시물이 올라올 때 현재 채널에서 알림을 받을 수 있습니다.\n\n"
            f"📌 **현재 채널**\n"
            f"- {guild.name} > {channel.name}\n\n"
            f"⚒️ **현재 채널 설정**\n"
            f"- 등록된 계정 : **{f'[{author_name}](https://space.bilibili.com/{host_mid})' if host_mid else '없음'}**\n"
            f"- 멘션 설정 : **{channel_mention if channel_mention else '없음'}**\n"
            f"- 번역 설정 : **{channel_translation}**"
        ),
        color=discord.Color.blue()
    )

# 돌아가기 버튼 로직
async def handle_back_button(interaction, view_class):
    channel_id = str(interaction.channel_id)
    channel_setting = await load_channel_setting()
    host_mid = channel_setting.get(channel_id, {}).get("host_mid", None)
    author_name = await get_author_name(host_mid) if host_mid else None
    channel_mention = channel_setting.get(channel_id, {}).get('mention', None)
    channel_translation = 'ON' if channel_setting.get(channel_id, {}).get('translation', None) else 'OFF'

    original_embed = create_notify_embed(
        interaction.guild, interaction.channel, host_mid, author_name, channel_mention, channel_translation
    )
    await interaction.response.edit_message(embed=original_embed, view=view_class(host_mid))

# 돌아가기 버튼 View
class ViewBackButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_back_button(interaction, ViewBiliNotify)

# 계정 삭제 View
class ViewRemoveAccount(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_back_button(interaction, ViewBiliNotify)

    # 계정을 삭제하는 버튼
    @discord.ui.button(emoji="⛔", label="삭제", style=discord.ButtonStyle.red)
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()

        if channel_setting[channel_id]["host_mid"]:
            host_mid = channel_setting[channel_id]["host_mid"]
            author_name = await get_author_name(host_mid)
            channel_setting[channel_id]["host_mid"] = ""
            await save_channel_setting(channel_setting)

            new_embed = discord.Embed(
                title="🚀 계정 삭제 완료!",
                description=f"현재 채널에 등록된 **[{author_name}](https://space.bilibili.com/{host_mid})** 계정을 삭제했습니다.",
                color=discord.Color.blue()
            )
        else:
            new_embed = discord.Embed(
                title="⚠️ 현재 채널에 등록된 계정이 없습니다.",
                color=discord.Color.blue()
            )
        await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())

# 번역 설정 View
class ViewTranslationSetting(discord.ui.View):
    def __init__(self, channel_setting, channel_id):
        super().__init__()
        self.update_button_label(channel_setting, channel_id)

    # 번역 설정 상태에 따라 버튼의 라벨 및 스타일 업데이트
    def update_button_label(self, channel_setting, channel_id):
        if channel_setting[channel_id]["translation"]:
            self.children[1].label = "번역 비활성화"
            self.children[1].emoji = "⛔"
            self.children[1].style = discord.ButtonStyle.red
        else:
            self.children[1].label = "번역 활성화"
            self.children[1].emoji = "✅"
            self.children[1].style = discord.ButtonStyle.green

    # 알림 설정 화면으로 돌아가는 버튼
    @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_back_button(interaction, ViewBiliNotify)

    # 번역 설정 버튼 - 활성화/비활성화 토글
    @discord.ui.button(emoji="✅", label="번역 활성화", style=discord.ButtonStyle.green, row=0)
    async def set_translation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_setting = await load_channel_setting()
        channel_id = str(interaction.channel_id)

        if channel_setting[channel_id]["translation"]:
            channel_setting[channel_id]["translation"] = False
            await save_channel_setting(channel_setting) 
            new_embed = discord.Embed(
                title="🚀 번역 비활성화 완료!",
                description=f"현재 채널의 번역 상태는 **OFF** 입니다.",
                color=discord.Color.blue()
            )
        else:
            channel_setting[channel_id]["translation"] = True
            await save_channel_setting(channel_setting) 
            new_embed = discord.Embed(
                title="🚀 번역 활성화 완료!",
                description=f"현재 채널의 번역 상태는 **ON** 입니다.",
                color=discord.Color.blue()
            )
        await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())   

# 멘션 설정 View
class ViewMentionSetting(discord.ui.View):
    def __init__(self, channel_setting, channel_id):
        super().__init__()
        self.update_button_label(channel_setting, channel_id)

    def update_button_label(self, channel_setting, channel_id):
        if channel_setting[channel_id]["mention"]:
            self.children[1].label = "역할 수정"
            self.children[1].emoji = "✏️"
        else:
            self.children[1].label = "멘션 활성화"
            self.children[1].emoji = "✅"

    # 알림 설정 화면으로 돌아가는 버튼
    @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_back_button(interaction, ViewBiliNotify)

    # 멘션 활성화 및 역할 추가 버튼
    @discord.ui.button(emoji="✅", label="멘션 활성화", style=discord.ButtonStyle.green, row=0)
    async def add_mention_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_mention(interaction)     

    # 멘션 비활성화 버튼
    @discord.ui.button(emoji="⛔", label="멘션 비활성화", style=discord.ButtonStyle.red, row=0)
    async def disable_mention_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.disable_mention(interaction)

    # 멘션을 추가할 역할을 선택할 드롭다운 메뉴 생성
    async def add_mention(self, interaction: discord.Interaction):
        # 서버의 모든 역할 가져오기
        roles = interaction.guild.roles[:]

        # 역할 선택 드롭다운 생성
        options = [
            discord.SelectOption(label=role.name, value=str(role.id)) for role in roles
        ]

        # 드롭다운 메뉴 생성
        select = Select(placeholder="역할을 선택하세요", options=options)

        # 드롭다운 메뉴 선택 이벤트 처리
        async def select_callback(interaction):
            channel_id = str(interaction.channel_id)
            selected_role_id = int(select.values[0])
            selected_role = interaction.guild.get_role(selected_role_id)
            selected_role_mention = f"@everyone" if selected_role == interaction.guild.default_role else f"<@&{selected_role.id}>"

            channel_setting = await load_channel_setting()

            if channel_setting[channel_id]["mention"]:
                embed_title = "🚀 역할 수정 완료!"
                embed_description = f"채널에 등록된 역할이 **{channel_setting[channel_id]['mention']}** 에서 **{selected_role_mention}** 로 변경되었습니다."
            else:
                embed_title= "🚀 역할 등록 완료!"
                embed_description = f"지금부터 새 게시물이 올라오면 **{selected_role_mention}** 역할에 멘션을 보냅니다."

            channel_setting[channel_id]["mention"] = selected_role_mention
            await save_channel_setting(channel_setting)

            new_embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())   

        select.callback = select_callback

        # View에 드롭다운 메뉴 추가
        view = View()
        view.add_item(select)

        new_embed = discord.Embed(
            title="🙍 역할 선택",
            description=f"멘션을 보낼 역할을 선택하세요.",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=new_embed, view=view)

    # 현재 멘션 설정을 비활성화
    async def disable_mention(self, interaction: discord.Interaction):
        channel_setting = await load_channel_setting()
        channel_id = str(interaction.channel_id)

        if channel_setting[channel_id]["mention"]:
            old_channel_mention = channel_setting[channel_id]["mention"]
            channel_setting[channel_id]["mention"] = ""
            await save_channel_setting(channel_setting) 
            new_embed = discord.Embed(
                title="🚀 멘션 비활성화 완료!",
                description=f"현재 채널에 등록된 **{old_channel_mention}** 멘션을 비활성화했습니다.",
                color=discord.Color.blue()
            )
        else:
            new_embed = discord.Embed(
                title="⚠️ 현재 채널의 멘션은 비활성화 상태입니다.",
                color=discord.Color.blue()
            )
        await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())   

# 알림설정 버튼 View
class ViewBiliNotify(discord.ui.View):
    def __init__(self, host_mid):
        super().__init__()
        self.update_button_label(host_mid)

    def update_button_label(self, host_mid):
        if host_mid:
            self.children[0].label = "계정 수정"
            self.children[0].emoji = "✏️"
        else:
            self.children[0].label = "계정 등록"
            self.children[0].emoji = "✅"

    # 계정 등록/수정 버튼 클릭 시 실행
    # - 현재 계정 정보가 있으면 수정, 없으면 등록
    @discord.ui.button(emoji="✅", label="계정 등록", style=discord.ButtonStyle.green, row=0)
    async def add_account_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        
        if channel_setting[channel_id]["host_mid"]:
            modal = AddAccountModal(self.change_account, 0) #수정
        else:
            modal = AddAccountModal(self.change_account, 1) #등록
        await interaction.response.send_modal(modal)

    # 계정 삭제 버튼 클릭 시 실행
    @discord.ui.button(emoji="⛔", label="계정 삭제", style=discord.ButtonStyle.red, row=0)
    async def remove_account_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_account(interaction)

    # 멘션 설정 버튼 클릭 시 실행
    @discord.ui.button(emoji="🔔", label="멘션 설정", style=discord.ButtonStyle.blurple, row=0)
    async def set_mention_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_mention(interaction)

    # 번역 설정 버튼 클릭 시 실행
    @discord.ui.button(emoji="🌐", label=" 번역 설정", style=discord.ButtonStyle.blurple, row=0)
    async def set_translate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_translation(interaction)

    # 계정 등록 또는 수정을 처리
    # - 새로운 계정 UID를 저장
    async def change_account(self, interaction: discord.Interaction, new_host_mid: str, options: int):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        old_host_mid = channel_setting[channel_id]["host_mid"]

        # watch_list.json에 새로운 UID 추가
        watch_list = await load_watch_list()
        if new_host_mid not in watch_list:
            watch_list.append(new_host_mid)
            await save_watch_list(watch_list)
            await create_host_mid_file(new_host_mid)

        # 채널 설정에 새로운 UID 저장
        channel_setting[channel_id]["host_mid"] = new_host_mid
        await save_channel_setting(channel_setting)

        # 등록/수정에 따라 메시지 다르게 생성
        if options: #등록
            new_author_name = await get_author_name(new_host_mid)
            new_embed = discord.Embed(
                title="🚀 계정 등록 완료!",
                description=f"현재 채널에 **[{new_author_name}](https://space.bilibili.com/{new_host_mid})** 계정이 등록되었습니다.\n계정에 새로운 게시물이 업로드되면 현재 채널에 알림을 보냅니다.",
                color=discord.Color.blue()
            )
        else: #수정
            old_author_name = await get_author_name(old_host_mid)
            new_author_name = await get_author_name(new_host_mid)
            new_embed = discord.Embed(
                title="🚀 계정 변경 완료!",
                description=f"현재 채널에 등록된 계정이 **[{old_author_name}](https://space.bilibili.com/{old_host_mid})** 에서 **[{new_author_name}](https://space.bilibili.com/{new_host_mid})** 로 변경되었습니다.\n계정에 새로운 게시물이 업로드되면 현재 채널에 알림을 보냅니다.",
                color=discord.Color.blue()
            )
        await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())        

    # 계정 삭제를 처리
    async def remove_account(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        host_mid = channel_setting[channel_id]["host_mid"]  # host_mid 가져오기

        if channel_id in channel_setting:
            if host_mid:
                author_name = await get_author_name(host_mid)
                new_embed = discord.Embed(
                    title="❗ 정말로 삭제하시겠습니까?",
                    description=f"현재 채널에 등록된 계정은 **[{author_name}](https://space.bilibili.com/{host_mid})** 입니다.",
                    color=discord.Color.blue()
                )
                await interaction.response.edit_message(embed=new_embed, view=ViewRemoveAccount())
            else:
                new_embed = discord.Embed(
                    title="⚠️ 현재 채널에 등록된 계정이 없습니다.",
                    color=discord.Color.blue()
                )
                await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())
        else:
            new_embed = discord.Embed(
                title="⚠️ 현재 채널에 등록된 계정이 없습니다.",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())

    # 멘션 설정 화면으로 이동
    async def set_mention(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        channel_mention = channel_setting[channel_id]["mention"]

        new_embed = discord.Embed(
            title="🔔 멘션 설정",
            description=(
                (f"현재 채널의 멘션 설정이 **{'ON' if channel_mention else 'OFF'}** 상태입니다.") +
                (f'\n현재 멘션을 받는 역할은 **{channel_mention}** 입니다.' if channel_mention else '')
            ),
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=new_embed, view=ViewMentionSetting(channel_setting, channel_id))   

    # 번역 설정 화면으로 이동
    async def set_translation(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        channel_translation = channel_setting[channel_id]["translation"]

        new_embed = discord.Embed(
            title="🌐 번역 설정",
            description=(
                f"현재 채널의 번역 설정이 **{'ON' if channel_translation else 'OFF'}** 상태입니다.\n"
                f"번역 설정을 켜면 현재 채널에 번역된 알림이 출력됩니다. "
            ),
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=new_embed, view=ViewTranslationSetting(channel_setting, channel_id))   

# 계정 등록 또는 수정을 위한 UID 입력 모달창
class AddAccountModal(Modal, title='비리비리 UID 입력'):
    host_mid = TextInput(label='bilibili UID', placeholder='알림을 받을 계정의 UID를 입력해 주세요.')

    # 모달창 초기화
    def __init__(self, callback, options):
        super().__init__()
        self.callback = callback
        self.options = options

    # 모달창 제출 시 호출되는 이벤트 핸들러
    async def on_submit(self, interaction: discord.Interaction):
        if not self.host_mid.value.isdigit():
            new_embed = discord.Embed(
                title="⚠️ 잘못된 UID 형식입니다.",
                description="UID는 숫자만 입력할 수 있습니다. 다시 시도해주세요.",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())
            return
        await self.callback(interaction, self.host_mid.value, self.options)

# Cog 정의
class BiliNotifySetting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="알림설정")
    async def set_bili_notify(self, interaction: discord.Interaction):
        """현재 채널의 bilibili 알림 설정을 변경할 수 있습니다."""

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

        # 채널 설정에 현재 채널 ID가 없는 경우 기본값 추가
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        if channel_id not in channel_setting:
            channel_setting[channel_id] = {"host_mid": "", "mention": "", "translation": False, "auto_translate": False}
            await save_channel_setting(channel_setting)

        # 채널 설정 정보 가져오기
        host_mid = channel_setting[channel_id].get("host_mid", None)
        author_name = await get_author_name(host_mid) if host_mid else None
        channel_mention = channel_setting[channel_id].get('mention', None)
        channel_translation = 'ON' if channel_setting[channel_id].get('translation', None) else 'OFF'

        # 알림 설정 메뉴 Embed 메시지 생성
        embed = create_notify_embed(
            interaction.guild, interaction.channel, host_mid, author_name, channel_mention, channel_translation
        )
        await interaction.response.send_message(embed=embed, view=ViewBiliNotify(host_mid), ephemeral=True)

    # UDS 파일 삭제
    def cleanup_uds_file(self):
        if os.path.exists(UDS_PATH):
            try:
                os.remove(UDS_PATH)
                print(f"[DEBUG] 기존 소켓 파일 {UDS_PATH} 삭제 완료")
            except Exception as e:
                print(f"[ERROR] 기존 소켓 파일 {UDS_PATH} 삭제 중 오류 발생: {e}")

    # UDS 모니터링
    async def monitor_signal(self):
        self.cleanup_uds_file()  # 기존 파일 삭제
        try:
            print("[DEBUG] monitor_signal() 시작 중...")
            server = await asyncio.start_unix_server(self.handle_signal, path=UDS_PATH)
            async with server:
                print("[DEBUG] UDS 서버가 시작되었습니다. 신호를 기다리고 있습니다...")
                await server.serve_forever()
        except Exception as e:
            print(f"[ERROR] monitor_signal() 실행 중 오류 발생: {e}")

    # UDS 신호 처리
    async def handle_signal(self, reader, writer):
        try:
            data = await reader.read(100)
            message = data.decode()
            if message.startswith('update:'):
                _, host_mid, post_id = message.split(':')
                await self.check_discord_channel(host_mid, post_id)
        except Exception as e:
            print(f"[ERROR] 신호 처리 중 오류 발생: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    # Discord 채널 메시지 처리
    async def check_discord_channel(self, host_mid: str, post_id: str):
        await self.bot.wait_until_ready()
        try:
            channel_setting = await load_channel_setting()
            channels = [
                channel_id
                for channel_id, settings in channel_setting.items()
                if settings.get("host_mid") == host_mid
            ]

            if channels:
                file_path = os.path.join('host_data', f"{host_mid}.json")
                if not os.path.exists(file_path):
                    print(f"[ERROR] {file_path} 파일이 존재하지 않습니다.")
                    return

                async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                    posts = json.loads(await file.read())
                    post = next((item for item in posts if item["id"] == post_id), None)
                    if not post:
                        print(f"[ERROR] {post_id}에 해당하는 게시물을 찾을 수 없습니다.")
                        return

                    for channel_id in channels:
                        channel = self.bot.get_channel(int(channel_id))
                        if not channel:
                            print(f"[ERROR] 유효하지 않은 채널 ID {channel_id}")
                            continue
                        try:
                            await send_notice_message(channel, post, host_mid, channel_id, channel_setting)
                        except Exception as e:
                            print(f"[ERROR] send_message 호출 중 예외 발생: {type(e).__name__} - {e}")

        except Exception as e:
            print(f"[ERROR] {host_mid}의 채널 메시지 전송 중 오류 발생: {e}")

async def setup(bot):
    bili_notify = BiliNotifySetting(bot)
    asyncio.create_task(bili_notify.monitor_signal())  # UDS 모니터링 시작
    await bot.add_cog(bili_notify)
