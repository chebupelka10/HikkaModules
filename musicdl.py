from telethon import types

from .. import loader, utils


@loader.tds
class MusicDLMod(loader.Module):
    """Download music"""

    strings = {
        "name": "MusicDL",
        "args": "🚫 Arguments not specified",
        "loading": "🔍 Loading...",
        "404": "🚫 Music {} not found",
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
            caption=f"🎧 {utils.ascii_face()}",
            reply_to=message.id,
        )
        if message.out:
            await message.delete()