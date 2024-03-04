from .. import loader, utils

@loader.tds
class YaMusicMod(loader.Module):
    """Модуль который показывает что вы слушаете сейчас на https://music.yandex.ru/ by @y9chepux"""
    strings = {"name": "YaMusic"}

    async def yanowcmd(self, message):
        """Показывает что вы слушаете на https://music.yandex.ru/ (Не работает для моей волны)"""
        await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji><b>Собираю данные о том, что вы слушаете на https://music.yandex.ru/</b>")
        try:
            results = await message.client.inline_query("@YaNowBot", "")
            await results[0].click(message.to_id, hide_via=True)
            await message.delete()
        except Exception as e:
            if "The bot did not answer to the callback query in time" in str(e):
                await utils.answer(message, "<emoji document_id=5312526098750252863>❌</emoji><b>Ошибка, вы слушаете трек в моей волне (Посмотрите help yamusic)</b>")
            else:
                await utils.answer(message, f"<emoji document_id=5312526098750252863>❌</emoji><b>Произошла ошибка: {e}</b>")

    async def yanowtrackcmd(self, message):
        """Отправляет трек, который вы слушаете на https://music.yandex.ru/ (Не работает для моей волны). Чтобы это работало, боту @YaNowBot нужно отправить /settings и указать в поле стандартный ответ (нет)"""
        await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji><b>Собираю данные о том, что вы слушаете на https://music.yandex.ru/</b>")
        try:
            results = await message.client.inline_query("@YaNowBot", "")
            await results[1].click(message.to_id , hide_via=True)
            await message.delete()
        except Exception as e:
            if "The bot did not answer to the callback query in time" in str(e):
                await utils.answer(message, "<emoji document_id=5312526098750252863>❌</emoji><b>Ошибка, вы слушаете трек в моей волне или вы не указали токен или вы не проделали что написанно в описании этой комманды (Посмотрите help yamusic)</b>")
            else:
                await utils.answer(message, f"<emoji document_id=5312526098750252863>❌</emoji><b>Произошла ошибка: {e}</b>")

    async def yasearchcmd(self, message):
        """Ищет треки по запросу на https://music.yandex.ru/"""
        args = utils.get_args(message)
        if args:
            await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji><b>Ищу трек на https://music.yandex.ru/</b>")
            try:
                results = await message.client.inline_query("@YaNowBot", " ".join(args))
                await results[0].click(message.to_id, hide_via=True)
                await message.delete()
            except Exception as e:
                if "The bot did not answer to the callback query in time" in str(e):
                    await utils.answer(message, "<emoji document_id=5312526098750252863>❌</emoji><b>Ошибка, попробуйте позже повторить запрос или вы не указали токен (Посмотрите help yanow)</b>")
                else:
                    await utils.answer(message, f"<emoji document_id=5312526098750252863>❌</emoji><b>Произошла ошибка: {e}</b>")
        else:
            await utils.answer(message, "<emoji document_id=5314591660192046611>❌</emoji><b>Вы не указали название песни</b>")

    async def yasettokencmd(self, message):
        """Команда чтобы сохранить ваш токен для входа в https://music.yandex.ru/. Инструкция как его получить: https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781/. Пример: .yasettoken VASH_TOKEN"""
        args = utils.get_args(message)
        if args:
            await utils.answer(message, "<emoji document_id=5307973935927663936>✅</emoji><b>Токен был успешно сохранен! Если после этого команды не работают, проверьте чат @YaNowBot</b>")
            await message.client.send_message("@YaNowBot", "/token " + " ".join(args))
        else:
            await utils.answer(message, "<emoji document_id=5314591660192046611>❌</emoji><b>Вы забыли указать токен (Инструкция как его получить: https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781)</b>")
