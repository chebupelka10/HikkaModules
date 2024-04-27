from telethon import types

from .. import loader, utils


@loader.tds
class MusicDLMod(loader.Module):
    """Download music"""

    strings = {
        "name": "MusicDL",
        "args": "<emoji document_id=5327834057977896553>👎</emoji> <b>Вы не указали название песни</b>",
        "loading": "<b><emoji document_id=5328273261333584797>💃</emoji> Ищу эту песню</b>",
        "404": "<emoji document_id=5327834057977896553>👎</emoji> <b>Данный трек {} не найден</b>",
    }

    async def client_ready(self, *_):
        self.musicdl = await self.import_lib(
            "https://libs.hikariatama.ru/musicdl.py",
            suspend_on_error=True,
        )

    @loader.command(ru_doc="<название> - Скачать песню")
    async def mdl(self, message: types.Message):
        """ - Download track"""
        args = utils.get_args_raw(message)
        if not args and message.is_reply:
            reply = await message.get_reply_message()
            args = reply.raw_text.replace(".mdl", "").strip()
        elif not args:
            await utils.answer(message, self.strings("args"))
            return

        message = await utils.answer(message, self.strings("loading"))
        result = await self.musicdl.dl(args, only_document=True)

        if not result:
            await utils.answer(message, self.strings("404").format(args))
            return

        await self._client.send_file(
            message.peer_id,
            result,
            caption=f"<b><emoji document_id=5328014223266030170>🎧</emoji> {utils.ascii_face()}</b>",
            reply_to=message.id,
        )
        if message.out:
            await message.delete()