# meta developer: @chepuxmodules

from .. import loader, utils

@loader.tds
class YaNowMod(loader.Module):
    """Модуль который показывает что вы слушаете сейчас на https://music.yandex.ru/ by @y9chepux"""
    strings = {"name": "YaNow"}

    async def yanowcmd(self, message):
        """Показывает что вы слушаете на https://music.yandex.ru/"""
        await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji><b>Собираю данные о том что вы слушаете на https://music.yandex.ru/</b>")
        results = await message.client.inline_query("@YaNowBot", "")
        if results:
            await results[0].click(message.to_id, hide_via=True)
            await message.delete()
        else:
            await utils.answer(message, "<emoji document_id=5314591660192046611>❌</emoji><b>Ошибка, попробуйте позже повторить запрос</b>")

    async def yasettokencmd(self, message):
        """Комманда чтобы сохранить ваш токен для входа в https://music.yandex.ru/. Инструкция как его получить: https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781/. Пример: .ysettoken VASH_TOKEN"""
        args = utils.get_args(message)
        if args:
            await utils.answer(message, "<emoji document_id=5307973935927663936>✅</emoji><b>Токен был успешно сохранен!</b>")
            await message.client.send_message("@YaNowBot", "/token " + " ".join(args))
            await message.delete()
        else:
            await utils.answer(message, "<emoji document_id=5312526098750252863>❌</emoji><b>Вы забыли указать token(Инструкция как его получить: https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781)")
