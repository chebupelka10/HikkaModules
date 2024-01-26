# meta developer: @chepuxmodules

from .. import loader, utils
from telethon import events
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

class BVideoMod(loader.Module):
    """Блокирует видео в чатах by @y9chebupelka"""
    strings = {"name": "Block video"}

    def __init__(self):
        self.name = self.strings["name"]
        self._me = None
        self._ratelimit = []
        self.blocked = {}

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self.me = await client.get_me()

    async def bvideocmd(self, message):
        """Блокирует видео в чатах"""
        chat = message.chat_id
        if chat not in self.blocked:
            self.blocked[chat] = []
            await message.edit("<b><emoji document_id=5312526098750252863>❌</emoji> Видео заблокированы в этом чате</b>")
        else:
            await message.edit("<b><emoji document_id=5314591660192046611>❌</emoji> Видео уже заблокированы в этом чате</b>")

    async def vidstatuscmd(self, message):
        """Показывает в каких чатах заблокированны видео"""
        chat = message.chat_id
        if chat in self.blocked and self.blocked[chat]:
            ids = ", ".join(str(id) for id in self.blocked[chat])
            await message.edit(f"<b><emoji document_id=5429452773747860261>❌</emoji> Видео заблокированы для этих пользователей: {ids}</b>")
        else:
            await message.edit("<b><emoji document_id=5308041633202182757>✔️</emoji> Видео не заблокированы для никого</b>")

    async def ubvideocmd(self, message):
        """Разблокирует видео в чатах"""
        chat = message.chat_id
        if chat in self.blocked:
            self.blocked.pop(chat)
            await message.edit("<b><emoji document_id=5314250708508220914>✅</emoji> Видео разблокированы в этом чате</b>")
        else:
            await message.edit("<b><emoji document_id=5321366563079595431>👍</emoji> Видео не были заблокированы в этом чате</b>")

    async def watcher(self, message):
        chat = message.chat_id
        sender = message.sender_id
        if chat in self.blocked and sender != self.me.id:
            if isinstance(message.media, (MessageMediaDocument, MessageMediaPhoto)):
                if message.media.document.mime_type.startswith("video/"):
                    await message.delete()
                    if sender not in self.blocked[chat]:
                        self.blocked[chat].append(sender)
