# -*- coding: utf-8 -*-
# meta developer: @yourusername

from .. import loader, utils
import telethon

@loader.tds
class GifBlockerMod(loader.Module):
    """Модуль для блокировки GIF в чатах"""
    strings = {"name": "GifBlocker"}

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def bgifcmd(self, message):
        """Блокирует GIF в чате"""
        chat_id = utils.get_chat_id(message)
        self.db.set("GifBlocker", "blockid", list(set(self.db.get("GifBlocker", "blockid", []) + [chat_id])))
        await message.edit("<b>GIF теперь заблокированы в этом чате</b>")

    async def ubgifcmd(self, message):
        """Разблокирует GIF в чате"""
        chat_id = utils.get_chat_id(message)
        blockid = self.db.get("GifBlocker", "blockid", [])
        if chat_id in blockid:
            blockid.remove(chat_id)
            self.db.set("GifBlocker", "blockid", blockid)
            await message.edit("<b>GIF теперь разблокированы в этом чате</b>")
        else:
            await message.edit("<b>GIF не были заблокированы в этом чате</b>")

    @loader.unrestricted
    async def watcher(self, event):
        """Проверяет сообщения на наличие GIF"""
        if isinstance(event, telethon.events.NewMessage.Event):
            if event.media and isinstance(event.media, telethon.types.MessageMediaDocument):
                if 'image/gif' in event.media.document.mime_type:
                    chat_id = utils.get_chat_id(event.message)
                    if chat_id in self.db.get("GifBlocker", "blockid", []):
                        await event.delete()