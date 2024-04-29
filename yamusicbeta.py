import asyncio
import logging
from asyncio import sleep

import aiohttp
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import Message
from yandex_music import ClientAsync

from .. import loader, utils

logger = logging.getLogger(__name__)
logging.getLogger("yandex_music").propagate = False


@loader.tds
class YmNowMod(loader.Module):
    """
    Module for yandex music. Based on SpotifyNow, YaNow and WakaTime. [BETA]
    """

    strings = {
        "name": "YmNow",
        "no_token": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Specify a token in"
            " config!</b>"
        ),
        "playing": (
            "<b><emoji document_id=5188705588925702510>🎶</emoji> Now playing:"
            " </b><code>{}</code><b> - </b><code>{}</code>\n<b>🕐 {}</b>"
        ),
        "no_args": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Provide arguments!</b>"
        ),
        "state": "🙂 <b>Widgets are now {}</b>\n{}",
        "tutorial": (
            "ℹ️ <b>To enable widget, send a message to a preferred chat with text"
            " </b><code>{YANDEXMUSIC}</code>"
        ),
        "no_results": (
            "<b><emoji document_id=5285037058220372959>☹️</emoji> No results found"
            " :(</b>"
        ),
        "autobioe": "<b>🔁 Autobio enabled</b>",
        "autobiod": "<b>🔁 Autobio disabled</b>",
        "lyrics": "<b>📜 Lyrics: \n{}</b>",
        "already_liked": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Current playing track"
            " is already liked!</b>"
        ),
        "liked": (
            "<b><emoji document_id=5310109269113186974>❤️</emoji> Liked current playing"
            " track!</b>"
        ),
        "not_liked": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Current playing track"
            " not liked!</b>"
        ),
        "disliked": (
            "<b><emoji document_id=5471954395719539651>💔</emoji> Disliked current"
            " playing track!</b>"
        ),
        "my_wave": (
            "<b><emoji document_id=5472377424228396503>🤭</emoji> You listening to track"
            " in my wave, I can't recognize it.</b>"
        ),
        "_cfg_yandexmusictoken": "Yandex.Music account token",
        "_cfg_autobiotemplate": "Template for AutoBio",
        "_cfg_automesgtemplate": "Template for AutoMessage",
        "_cfg_update_interval": "Update interval",
        "no_lyrics": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Track doesn't have"
            " lyrics.</b>"
        ),
        "guide": (
            '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">Instructions'
            " for obtaining a Yandex.Music token</a>"
        ),
        "configuring": "🙂 <b>Widget is ready and will be updated soon</b>",
    }

    strings_ru = {
        "no_token": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи токен в"
            " конфиге!</b>"
        ),
        "playing": (
            "<b><emoji document_id=5188705588925702510>🎶</emoji> Сейчас играет:"
            " </b><code>{}</code><b> - </b><code>{}</code>\n<b>🕐 {}</b>"
        ),
        "no_args": (
            "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи аргументы!</b>"
        ),
        "state": "🙂 <b>Виджеты теперь {}</b>\n{}",
        "tutorial": (
            "ℹ️ <b>Чтобы включить виджет, отправь сообщение в нужный чат с текстом"
            " </b><code>{YANDEXMUSIC}</code>"
        ),
        "no_results": (
            "<b><emoji document_id=5285037058220372959>☹️</emoji> Ничего не найдено"
            " :(</b>"
        ),
        "autobioe": "<b>🔁 Autobio включен</b>",
        "autobiod": "<b>🔁 Autobio выключен</b>",
        "lyrics": "<b>📜 Текст песни: \n{}</b>",
        "_cls_doc": (
            "Модуль для Яндекс.Музыка. Основан на SpotifyNow, YaNow и WakaTime. [BETA]"
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
            "<b><emoji document_id=5472377424228396503>🤭</emoji> Ты слушаешь трек в"
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
                last_queue = await client.queue(queues[0].id)

                try:
                    last_track_id = last_queue.get_current_track()
                    last_track = await last_track_id.fetch_track_async()
                except:
                    return

                artists = ", ".join(last_track.artists_name())
                title = last_track.title
                try:
                    await self.client.edit_message(
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

    async def on_unload(self):
        self._task.cancel()

    @loader.command()
    async def automsgcmd(self, message: Message):
        """Toggle YandexMusic widgets' updates(sample: https://t.me/vsecoder_bio/24)"""
        state = not self.get("state", False)
        self.set("state", state)
        await utils.answer(
            message,
            self.strings("state").format(
                "on" if state else "off", self.strings("tutorial") if state else ""
            ),
        )

    @loader.command()
    async def ynowcmd(self, message: Message):
        """Get now playing track"""

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
            (
                f"{last_track.duration_ms // 1000 // 60:02}:{last_track.duration_ms // 1000 % 60:02}"
            ),
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
    async def ylyrics(self, message: Message):
        """Get now playing track lyrics"""

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
        last_queue = await client.queue(queues[0].id)

        try:
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

            if not lyric.strip():
                await utils.answer(message, self.strings["no_lyrics"])
                return

            await utils.answer(
                message, self.strings["lyrics"].format(utils.escape_html(lyric))
            )
        except:
            await utils.answer(message, self.strings["no_lyrics"])

    @loader.command()
    async def ylike(self, message: Message):
        """Like now playing track"""

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

        try:
            await client.tracks_like(last_track.id)
            await utils.answer(message, self.strings["liked"])
        except Exception as e:
            if "already" in str(e):
                await utils.answer(message, self.strings["already_liked"])
            else:
                await utils.answer(message, str(e))

    @loader.command()
    async def ydislike(self, message: Message):
        """Dislike now playing track"""

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

        try:
            await client.tracks_dislike(last_track.id)
            await utils.answer(message, self.strings["disliked"])
        except Exception as e:
            if "not" in str(e):
                await utils.answer(message, self.strings["not_liked"])
            else:
                await utils.answer(message, str(e))
