import discord
from file_io import load_channel_setting, save_channel_setting, get_author_name
from file_io import load_watch_list, save_watch_list, create_host_mid_file
from discord.ui import Button, View, Modal, TextInput, Select

# ------------------ 번역 설정 버튼 ------------------
# 번역 설정을 활성화/비활성화할 수 있는 버튼 View
class ViewSetTranslationButton(discord.ui.View):
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
        # set_bili_notify에서 처음 보낸 ViewBiliNotify로 돌아가도록 설정
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        host_mid = channel_setting.get(channel_id, {}).get("host_mid", None)
        author_name = await get_author_name(host_mid) if host_mid else None
        channel_mention = channel_setting.get(channel_id, {}).get('mention', None)
        channel_translation = 'ON' if channel_setting.get(channel_id, {}).get('translation', None) else 'OFF'

        original_embed = discord.Embed(
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
        await interaction.response.edit_message(embed=original_embed, view=ViewBiliNotify(host_mid))

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

# ------------------ 계정 삭제 버튼 ------------------
# 계정 삭제 확인을 위한 버튼 View
class ViewRemoveAccountButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    # 알림 설정 화면으로 돌아가는 버튼
    @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # set_bili_notify에서 처음 보낸 ViewBiliNotify로 돌아가도록 설정
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        host_mid = channel_setting.get(channel_id, {}).get("host_mid", None)
        author_name = await get_author_name(host_mid) if host_mid else None
        channel_mention = channel_setting.get(channel_id, {}).get('mention', None)
        channel_translation = 'ON' if channel_setting.get(channel_id, {}).get('translation', None) else 'OFF'

        original_embed = discord.Embed(
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
        await interaction.response.edit_message(embed=original_embed, view=ViewBiliNotify(host_mid))

    # 계정을 삭제하는 버튼
    @discord.ui.button(emoji="⛔", label="삭제", style=discord.ButtonStyle.red)
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()

        if channel_id in channel_setting:
            if channel_setting[channel_id]["host_mid"]:
                host_mid = channel_setting[channel_id]["host_mid"]  # host_mid 가져오기
                author_name = await get_author_name(host_mid)
                channel_setting[channel_id]["host_mid"] = ""  # host_mid를 빈 문자열로 초기화
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
        else:
            new_embed = discord.Embed(
                title="⚠️ 현재 채널에 등록된 계정이 없습니다.",
                color=discord.Color.blue()
            )
        await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())

# ------------------ 멘션 설정 버튼 ------------------
# 멘션 설정을 관리할 수 있는 버튼 View.
# - 멘션 활성화, 비활성화, 역할 수정 가능
class ViewSetMentionButton(discord.ui.View):
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
        # set_bili_notify에서 처음 보낸 ViewBiliNotify로 돌아가도록 설정
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        host_mid = channel_setting.get(channel_id, {}).get("host_mid", None)
        author_name = await get_author_name(host_mid) if host_mid else None
        channel_mention = channel_setting.get(channel_id, {}).get('mention', None)
        channel_translation = 'ON' if channel_setting.get(channel_id, {}).get('translation', None) else 'OFF'

        original_embed = discord.Embed(
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
        await interaction.response.edit_message(embed=original_embed, view=ViewBiliNotify(host_mid))

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

# ------------------ 처음으로 돌아가기 버튼 ------------------
# 처음으로 돌아가기 버튼 View
# - 이전 화면으로 돌아가도록 설정
class ViewBackButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    # '돌아가기' 버튼 클릭 시 호출되는 이벤트 핸들러
    # - 알림 설정 화면으로 돌아갑니다
    @discord.ui.button(emoji="⬅️", label="돌아가기", style=discord.ButtonStyle.grey)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # set_bili_notify에서 처음 보낸 ViewBiliNotify로 돌아가도록 설정
        channel_id = str(interaction.channel_id)
        channel_setting = await load_channel_setting()
        host_mid = channel_setting.get(channel_id, {}).get("host_mid", None)
        author_name = await get_author_name(host_mid) if host_mid else None
        channel_mention = channel_setting.get(channel_id, {}).get('mention', None)
        channel_translation = 'ON' if channel_setting.get(channel_id, {}).get('translation', None) else 'OFF'

        original_embed = discord.Embed(
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
        await interaction.response.edit_message(embed=original_embed, view=ViewBiliNotify(host_mid))
        
# ------------------ 계정 등록/수정 입력 모달창 ------------------
# 계정 등록 또는 수정을 위한 UID 입력 모달창
class AddAccountModal(Modal, title='비리비리 UID 입력'):
    host_mid = TextInput(label='bilibili UID', placeholder='알림을 받을 계정의 UID를 입력해 주세요.')

    # 모달창 초기화
    # - callback: 입력 값 처리 콜백 함수
    # - options: 등록(1) 또는 수정(0) 옵션
    def __init__(self, callback, options):
        super().__init__()
        self.callback = callback
        self.options = options

    # 모달창 제출 시 호출되는 이벤트 핸들러
    # - UID가 유효하지 않으면 오류 메시지를 표시
    # - 유효한 경우 콜백 함수 호출
    async def on_submit(self, interaction: discord.Interaction):
        # 숫자가 아닌 값이 입력된 경우
        if not self.host_mid.value.isdigit():
            new_embed = discord.Embed(
                title="⚠️ 잘못된 UID 형식입니다.",
                description="UID는 숫자만 입력할 수 있습니다. 다시 시도해주세요.",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=new_embed, view=ViewBackButton())        
            return  # 콜백을 호출하지 않고 종료

        # UID가 유효한 경우 콜백 호출
        await self.callback(interaction, self.host_mid.value, self.options)

# ------------------ /알림관리 명령어 버튼 구성 View ------------------
# /알림관리 명령어를 위한 버튼 View
# - 계정 등록/수정, 삭제, 멘션 설정, 번역 설정 등을 관리
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
                await interaction.response.edit_message(embed=new_embed, view=ViewRemoveAccountButton())
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
        await interaction.response.edit_message(embed=new_embed, view=ViewSetMentionButton(channel_setting, channel_id))   

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
        await interaction.response.edit_message(embed=new_embed, view=ViewSetTranslationButton(channel_setting, channel_id))   

# ------------------ 사전예약 순위 페이지 출력 View ------------------
# 비리비리 사전예약 게임 순위를 페이지 형식으로 출력하는 View
class BiliPreRankView(discord.ui.View):
    # 초기화 메서드
    # - pre_rank: 사전예약 게임 데이터 리스트
    # - embeds_per_page: 한 페이지에 표시할 게임 Embed 개수 (기본값: 5)
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
    # - 사전예약 게임 정보를 페이지 단위로 나눠 Embed 형태로 반환
    def generate_embeds(self):
        embeds = []
        start = self.current_page * self.embeds_per_page
        end = start + self.embeds_per_page
        n = start + 1
        for game in self.pre_rank[start:end]:
            game_tag = " ".join([f"`#{tag}`" for tag in game.get('tag_names', [])])
            #description = game.get('game_desc', '').replace('\n', ' ') + "....." + f"\n\n`#{game.get('category', '')}` {game_tag}"
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
            embed.set_thumbnail(url=icon_url) if icon_url.startswith("https://") else None
            embed.set_author(name=f"{n}")
            embeds.append(embed)
            n += 1
        return embeds

# ------------------ 사전예약 페이지 네비게이션 버튼 ------------------
# 사전예약 순위 이전 페이지 버튼
class PreviousPageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="⬅️ 이전 페이지", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view  # 버튼이 속한 뷰 객체를 참조
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
        view = self.view  # 버튼이 속한 뷰 객체를 참조
        if isinstance(view, BiliPreRankView):
            view.current_page += 1
            view.update_buttons()
            embeds = view.generate_embeds()
            await interaction.response.edit_message(embeds=embeds, view=view)