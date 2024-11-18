import discord
from discord.ext import commands
from utils import translate_text_deepl, is_message_chinese, is_not_korean

class AutoTranslate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 메시지 이벤트 처리: 중국어 메시지 자동 번역
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return  # 봇의 메시지는 무시

        # 중국어 메시지 감지
        #if is_message_chinese(message.content):  
        #    # 메시지 전송 권한 확인
        #    permissions = message.channel.permissions_for(message.guild.me)
        #    if not permissions.send_messages:  
        #        return
        #    
        #    translated_text = await translate_text_deepl(message.content)
        #    response = f"**`중국어 자동 번역됨`**\n{translated_text}"
        #    await message.channel.send(response)

        # 한글 외 메시지 감지
        if is_not_korean(message.content):  
            # 메시지 전송 권한 확인
            permissions = message.channel.permissions_for(message.guild.me)
            if not permissions.send_messages:  
                return
            
            translated_text = await translate_text_deepl(message.content)
            response = f"**`자동 번역됨`**\n{translated_text}"
            await message.channel.send(response)

# Cog을 봇에 추가하는 함수
async def setup(bot: commands.Bot):
    await bot.add_cog(AutoTranslate(bot))
