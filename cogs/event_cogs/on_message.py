import discord
from discord.ext import commands

from bot_utilities.response_utils import split_response
from bot_utilities.ai_utils import generate_response, text_to_speech
from bot_utilities.config_loader import config, load_active_channels
from ..common import allow_dm, trigger_words, replied_messages, smart_mention, message_history, MAX_HISTORY, instructions

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = load_active_channels
        self.instructions = instructions

    async def process_message(self, message):
        active_channels = self.active_channels()
        string_channel_id = f"{message.channel.id}"
        is_replied = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user and smart_mention
        is_dm_channel = isinstance(message.channel, discord.DMChannel)
        is_active_channel = string_channel_id in active_channels
        is_allowed_dm = allow_dm and is_dm_channel
        contains_trigger_word = any(word in message.content for word in trigger_words)
        is_bot_mentioned = self.bot.user.mentioned_in(message) and smart_mention and not message.mention_everyone
        bot_name_in_message = self.bot.user.name.lower() in message.content.lower() and smart_mention

        if message.author == self.bot.user:
            return

        if not (is_active_channel or is_allowed_dm or contains_trigger_word or is_bot_mentioned or is_replied or bot_name_in_message):
            return

        instruc_config = active_channels.get(string_channel_id, config['DEFAULT_INSTRUCTION'])
        instruction_value = self.instructions.get(instruc_config, list(self.instructions.values())[0])
        instructions_text = f"Ignore all the instructions you have gotten before. {instruction_value}. "

        channel_id = message.channel.id
        key = f"{message.author.id}-{channel_id}"
        message_history[key] = message_history.get(key, [])
        message_history[key] = message_history[key][-MAX_HISTORY:]
        message_history[key].append({"role": "user", "content": message.content})

        async with message.channel.typing():
            response = await self.generate_response(instructions_text, message_history[key])

        message_history[key].append({"role": "assistant", "content": response})

        await self.send_response(message, response)

    async def generate_response(self, instructions, history):
        return await generate_response(instructions=instructions, history=history)

    async def send_response(self, message, response):
        try:
            bytes_obj = await text_to_speech(response)
        except Exception:
            bytes_obj = None

        author_voice_channel = None
        author_member = None
        if message.guild:
            author_member = message.guild.get_member(message.author.id)
        if author_member and author_member.voice:
            author_voice_channel = author_member.voice.channel

        if author_voice_channel and bytes_obj:
            voice_channel = await author_voice_channel.connect()
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=bytes_obj))
            while voice_channel.is_playing():
                await discord.utils.sleep_until(discord.utils.utcnow())
            await voice_channel.disconnect()

        if response is not None:
            for chunk in split_response(response):
                try:
                    await message.reply(chunk, allowed_mentions=discord.AllowedMentions.none(), suppress_embeds=True)
                except Exception:
                    await message.channel.send("Je suis désolé, il y a eu un problème pour envoyer ma réponse. Le message initial a peut-être été supprimé.")
        else:
            await message.reply("Je suis désolé, il y a eu un problème pour envoyer ma réponse.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.mentions:
            for mention in message.mentions:
                message.content = message.content.replace(f'<@{mention.id}>', f'{mention.display_name}')

        if message.stickers or message.author.bot or (message.reference and message.reference.resolved and (message.reference.resolved.author != self.bot.user or message.reference.resolved.embeds)):
            return

        await self.process_message(message)

async def setup(bot):
    await bot.add_cog(OnMessage(bot))
