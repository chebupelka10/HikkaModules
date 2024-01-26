# Name: musicdl
# Description: Download music by hikariatama (modded by @y9chebupelka)
# Commands:
# .mdl
# meta developer: @chepuxmodules

from telethon.tl.types import Message
from .. import loader, utils

@loader.tds
class MusicDLMod(loader.Module):
    """Download music by hikariatama (modded by @y9chebupelka)"""

    strings = {
        "name": "MusicDL",
        "args": "<emoji document_id=5314591660192046611>❌</emoji> <b>Arguments not specified</b>",
        "loading": "<emoji document_id=5323333310208810193>😀</emoji> <b>Loading...</b>",
        "404": "<emoji document_id=5312526098750252863>❌</emoji> <b>Music </b><code>{}</code><b> not found</b>",
    }

    strings_ru = {
        "args": "<<emoji document_id=5314591660192046611>❌</emoji> <b>Не указаны аргументы</b>",
        "loading": "<emoji document_id=5323333310208810193>😀</emoji> <b>Загрузка...</b>",
        "404": "<emoji document_id=5312526098750252863>❌</emoji> <b>Песня </b><code>{}</code><b> не найдена</b>",
    }

    async def client_ready(self, *_):
        self.musicdl = await self.import_lib(
            "https://libs.hikariatama.ru/musicdl.py",
            suspend_on_error=True,
        )

    @loader.command(ru_doc="<название> - Скачать песню")
    async def mdl(self, message: Message):
        """<name> - Download track"""
        
        if message.is_reply:
            reply = await message.get_reply_message()
            args = reply.raw_text
        else:
            
            args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings["args"])
            return
        
        args = args.replace(".m", "") 
        
        message = await utils.answer(message, self.strings["loading"])
        
        result = await self.musicdl.dl(args, only_document=True)
       
        if not result:
            await utils.answer(message, self.strings["404"].format(args))
            return
        
        await self._client.send_file(
            message.peer_id,
            result,
            caption=f" <b><emoji document_id=5321366563079595431>👍</emoji>{args.title()}</b>", 
            reply_to=getattr(message, "reply_to_msg_id", None),
        )
        
        if message.out:
            await message.delete()
