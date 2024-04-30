import asyncio
import logging
import aiohttp
from asyncio import sleep
from yandex_music import ClientAsync
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from telethon.tl.functions.account import UpdateProfileRequest
from .. import loader, utils  # type: ignore
from telethon import types

logger = logging.getLogger(__name__)
logging.getLogger("yandex_music").propagate = False


@loader.tds
class YaNowMod(loader.Module):
    """
    Module to control Yandex Music. Based on unofficial api, and ymnow module. by @nyachepux
    """
    strings = {
        "name": "YaMusic",
        "no_token": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи токен в"
            " конфиге!</b>"
        ),
        "args": "<emoji document_id=5327834057977896553>👎</emoji> <b>Вы не указали название песни</b>",
        "loading": "<b><emoji document_id=5328273261333584797>💃</emoji> Ищу эту песню</b>",
        "404": "<emoji document_id=5327834057977896553>👎</emoji> <b>Данный трек {} не найден</b>",
        "playing": (
            "<b><emoji document_id=5188705588925702510>🎶</emoji> Сейчас играет:"
            " </b><code>{}</code><b> - </b><code>{}</code>\n<emoji document_id=5463424079568584767>🎧</emoji><b> Слушаю трек на Яндекс.Музыка</b>\n<b><emoji document_id=6030821505984630931>🕐</emoji> Трек длится: {}</b>"
        ),
        "no_args": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи аргументы!</b>"
        ),
        "state": "<emoji document_id=5462969861007219468>🙂</emoji> <b>Виджеты теперь {}</b>\n{}",
        "tutorial": (
            "ℹ️ <b>Чтобы включить виджет, отправь сообщение в нужный чат с текстом"
            " </b><code>{YANDEXMUSIC}</code>"
        ),
        "no_results": (
            "<b><emoji document_id=5285037058220372959>☹️</emoji> Ничего не найдено"
            " :(</b>"
        ),
        "autobioe": "<b><emoji document_id=6030657343744644592>🔁</emoji> Autobio включен</b>",
        "autobiod": "<b><emoji document_id=6030657343744644592>🔁</emoji> Autobio выключен</b>",
        "lyrics": "<b><emoji document_id=6030742019024883631>📄</emoji> Текст песни: \n{}</b>",
        "_cls_doc": (
            "Module to control Yandex Music. Based on unofficial api, and ymnow module. by @nyachepux"
        ),
        "already_liked": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Текущий трек уже"
            " лайкнут!</b>"
        ),
        "liked": (
            "<b><emoji document_id=5310109269113186974>❤️</emoji> Лайкнул текущий"
            " трек!</b>"
        ),
        "not_liked": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Текущий трек не"
            " лайкнут!</b>"
        ),
        "disliked": (
            "<b><emoji document_id=5471954395719539651>💔</emoji> Дизлайкнул текущий"
            " трек!</b>"
        ),
        "my_wave": (
            "<b><emoji document_id=5327834057977896553>👎</emoji> Ты слушаешь трек в"
            " Моей Волне, я не могу распознать его.</b>"
        ),
        "_cfg_yandexmusictoken": "Токен аккаунта Яндекс.Музыка",
        "_cfg_autobiotemplate": "Шаблон для AutoBio",
        "_cfg_automesgtemplate": "Шаблон для AutoMessage",
        "_cfg_update_interval": "Интервал обновления виджета",
        "no_lyrics": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> У трека нет"
            " текста!</b>"
        ),
        "guide": (
            '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">Инструкция'
            " по получению токена Яндекс.Музыка</a>"
        ),
        "configuring": "🙂 <b>Виджет готов и скоро будет обновлен</b>",
    }
 

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "YandexMusicToken",
                None,
                lambda: self.strings["_cfg_yandexmusictoken"],
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "AutoBioTemplate",
                "🎧 {}",
                lambda: self.strings["_cfg_autobiotemplate"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "AutoMessageTemplate",
                "🎧 {}",
                lambda: self.strings["_cfg_automesgtemplate"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "update_interval",
                300,
                lambda: self.strings["_cfg_update_interval"],
                validator=loader.validators.Integer(minimum=100),
            ),
        )

    async def on_dlmod(self):
        if not self.get("guide_send", False):
            await self.inline.bot.send_message(
                self._tg_id,
                self.strings["guide"],
            )
            self.set("guide_send", True)

    async def client_ready(self, client: TelegramClient, db):
        self.client = client
        self.db = db

        self._premium = getattr(await self.client.get_me(), "premium", False)

        self.set("widgets", list(map(tuple, self.get("widgets", []))))

        self._task = asyncio.ensure_future(self._parse())

        if self.get("autobio", False):
            self.autobio.start()

    async def _parse(self, do_not_loop: bool = False):
        while True:
            for widget in self.get("widgets", []):
                client = ClientAsync(self.config["YandexMusicToken"])

                await client.init()
                queues = await client.queues_list()

                try:
                    last_queue = await client.queue(queues[0].id)
                    last_track_id = last_queue.get_current_track()
                    last_track = await last_track_id.fetch_track_async()
                except:
                    return

                artists = ", ".join(last_track.artists_name())
                title = last_track.title
                try:
                    await self._client.edit_message(
                        *widget[:2],
                        self.config["AutoMessageTemplate"].format(
                            f"{artists} - {title}"
                            + (f" ({last_track.version})" if last_track.version else "")
                        ),
                    )
                except MessageNotModifiedError:
                    pass
                except FloodWaitError:
                    pass
                except Exception:
                    logger.debug("YmNow widget update failed")
                    self.set(
                        "widgets", list(set(self.get("widgets", [])) - set([widget]))
                    )
                    continue

            if do_not_loop:
                break

            await asyncio.sleep(int(self.config["update_interval"]))

    @loader.command()
    async def yaautomsgcmd(self, message: Message):
        """Включает/выключает виджет Яндекс Музыки"""
        state = not self.get("state", False)
        self.set("state", state)
        await utils.answer(
            message,
            self.strings["state"].format(
                "on" if state else "off", self.strings("tutorial") if state else ""
            ),
        )

    @loader.command()
    async def yanowcmd(self, message: Message):
        """Показывает что вы слушаете на Яндекс.Музыка"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except:
            await utils.answer(message, self.strings["no_token"])
            return
        try:
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
        except:
            await utils.answer(message, self.strings["my_wave"])
            return
        try:
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
        except:
            await utils.answer(message, self.strings["my_wave"])
            return

        info = await client.tracks_download_info(last_track.id, True)
        link = info[0].direct_link

        artists = ", ".join(last_track.artists_name())
        title = last_track.title
        if last_track.version:
            title += f" ({last_track.version})"
        else:
            pass

        caption = self.strings["playing"].format(
            utils.escape_html(artists),
            utils.escape_html(title),
            f"{last_track.duration_ms // 1000 // 60:02}:{last_track.duration_ms // 1000 % 60:02}",
        )
        try:
            lnk = last_track.id.split(":")[1]
        except:
            lnk = last_track.id
        else:
            pass

        await self.inline.form(
            message=message,
            text=caption,
            reply_markup={
                "text": "song.link",
                "url": f"https://song.link/ya/{lnk}",
            },
            silent=True,
            audio={
                "url": link,
                "title": utils.escape_html(title),
                "performer": utils.escape_html(artists),
            },
        )

    @loader.command()
    async def yalyrics(self, message: Message):
        """Показывает текст песни которую вы слушаете"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except:
            await utils.answer(message, self.strings["no_token"])
            return

        queues = await client.queues_list()

        try:
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
        except:
            await utils.answer(message, self.strings["my_wave"])
            return

        try:
            lyrics = await client.tracks_lyrics(last_track.id)
            async with aiohttp.ClientSession() as session:
                async with session.get(lyrics.download_url) as request:
                    lyric = await request.text()

            text = self.strings["lyrics"].format(utils.escape_html(lyric))
        except:
            text = self.strings["no_lyrics"]

        await utils.answer(message, text)

    @loader.command()
    async def yabio(self, message: Message):
        """Показывает трек который вы слушаете в описании вашего профиля"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except:
            await utils.answer(message, self.strings["no_token"])
            return

        current = self.get("autobio", False)
        new = not current
        self.set("autobio", new)

        if new:
            await utils.answer(message, self.strings["autobioe"])
            self.autobio.start()
        else:
            await utils.answer(message, self.strings["autobiod"])
            self.autobio.stop()

    async def yalikecmd(self, message: Message):
        """❤ Ставит лайк на трек который вы слушаете"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
        except:
            await utils.answer(message, self.strings["my_wave"])
            return

        try:
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
        except:
            await utils.answer(message, self.strings["my_wave"])
            return

        liked_tracks = await client.users_likes_tracks()
        liked_tracks = await liked_tracks.fetch_tracks_async()

        if isinstance(liked_tracks, list):
            if last_track in liked_tracks:
                await utils.answer(message, self.strings["already_liked"])
                return
            else:
                await last_track.like_async()
                await utils.answer(message, self.strings["liked"])
        else:
            await last_track.like_async()
            await utils.answer(message, self.strings["liked"])

    async def yadislikecmd(self, message: Message):
        """💔 Ставит дизлайк на трек который вы слушаете"""

        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except:
            logging.info("Указан неверный токен!")
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
        except:
            await utils.answer(message, self.strings["my_wave"])
            return

        try:
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
        except:
            await utils.answer(message, self.strings["my_wave"])
            return

        liked_tracks = await client.users_likes_tracks()
        liked_tracks = await liked_tracks.fetch_tracks_async()

        if isinstance(liked_tracks, list):
            if last_track in liked_tracks:
                await last_track.dislike_async()
                await utils.answer(message, self.strings["disliked"])

            else:
                await utils.answer(message, self.strings["not_liked"])
                return

        else:
            await utils.answer(message, self.strings["not_liked"])
            return

    @loader.loop(interval=60)
    async def autobio(self):
        client = ClientAsync(self.config["YandexMusicToken"])

        await client.init()
        try:
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
        except:
            return

        last_track_id = last_queue.get_current_track()

        last_track = await last_track_id.fetch_track_async()

        artists = ", ".join(last_track.artists_name())
        title = last_track.title

        text = self.config["AutoBioTemplate"].format(
            f"{artists} - {title}"
            + (f" ({last_track.version})" if last_track.version else "")
        )

        try:
            await self.client(
                UpdateProfileRequest(about=text[: 70])
            )
        except FloodWaitError as e:
            logger.info(f"Sleeping {e.seconds}")
            await sleep(e.seconds)
            return

    async def client_ready(self, *_):
        self.musicdl = await self.import_lib(
            "https://libs.hikariatama.ru/musicdl.py",
            suspend_on_error=True,
        )

    @loader.command
    async def yasearchcmd(self, message: types.Message):
        """Ищет треки на Яндекс.Музыка по названию"""
        args = utils.get_args_raw(message)
        if not args and message.is_reply:
            reply = await message.get_reply_message()
            args = reply.raw_text.replace(".yasearch", "").strip()
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