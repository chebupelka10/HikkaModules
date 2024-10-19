# meta developer: @chepuxmodules

import asyncio
import logging
import aiohttp
from asyncio import sleep
import os
import aiofiles
from yandex_music import ClientAsync
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from telethon.tl.functions.account import UpdateProfileRequest
from .. import loader, utils  # type: ignore

logger = logging.getLogger(__name__)
logging.getLogger("yandex_music").propagate = False
    
@loader.tds
class YaMusicMod(loader.Module):
    """
    Модуль для Яндекс.Музыки. Основан на YmNow от vsecoder. Создатель: @RemoveWoman [BETA]
    """
    strings = {
        "name": "YaMusic",
        "no_token": "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи токен в конфиге!</b>",
        "playing": "<b><emoji document_id=6030440409241488777>🎵</emoji> Сейчас играет: </b><code>{}</code><b> - </b><code>{}</code>\n<b><emoji document_id=6030802195811669198>🎵</emoji> Плейлист:</b> <code>{}</code>\n<b><emoji document_id=6030821505984630931>🕐</emoji> Длинна трека: {}</b>\n\n<emoji document_id=5463424079568584767>🎧</emoji> <b>Слушаю на Яндекс.Музыке</b>\n\n<b><emoji document_id=6030333284167192486>🔗</emoji> <a href=\"{}\">Открыть в Яндекс.Музыке</a>\n<emoji document_id=6030333284167192486>🔗</emoji> <a href=\"{}\">Открыть на song.link</a></b>",
        "no_args": "<b><emoji document_id=5843952899184398024>🚫</emoji> Укажи аргументы!</b>",
        "state": "<emoji document_id=6030742019024883631>📄</emoji> <b>Виджеты теперь {}</b>\n{}",
        "tutorial": (
            "ℹ️ <b>Чтобы включить виджет, отправь сообщение в нужный чат с текстом"
            " </b><code>{YANDEXMUSIC}</code>"
        ),
        "no_results": "<b><emoji document_id=5285037058220372959>☹️</emoji> Ничего не найдено :(</b>",
        "autobioe": "<b>🔁 Autobio включен</b>",
        "autobiod": "<b>🔁 Autobio выключен</b>",
        "lyrics": "<b><emoji document_id=6030742019024883631>📄</emoji> Текст песни <code>{}</code> - <code>{}</code>: \n{}</b>",
        "_cls_doc": "Модуль для Яндекс.Музыка. Основан на YmNow от vsecoder. Создатель: @RemoveWoman [BETA]",
        "already_liked": "<b><emoji document_id=5843952899184398024>🚫</emoji> Текущий трек уже лайкнут!</b>",
        "liked": "<b><emoji document_id=5310109269113186974>❤️</emoji> Лайкнул текущий трек!</b>",
        "not_liked": "<b><emoji document_id=5843952899184398024>🚫</emoji> Текущий трек не лайкнут!</b>",
        "disliked": "<b><emoji document_id=5471954395719539651>💔</emoji> Дизлайкнул текущий трек!</b>",
        "my_wave": "<b><emoji document_id=5472377424228396503>🤭</emoji> Я до сих пор не могу найти трек. Отпиши @RemoveWoman</b>",
        "_cfg_yandexmusictoken": "Токен аккаунта Яндекс.Музыка",
        "_cfg_autobiotemplate": "Шаблон для AutoBio",
        "_cfg_automesgtemplate": "Шаблон для AutoMessage",
        "_cfg_update_interval": "Интервал обновления виджета и био",
        "no_lyrics": "<b><emoji document_id=5843952899184398024>🚫</emoji> У трека нет текста!</b>",
        "guide": (
            '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">'
            "Инструкция по получению токена Яндекс.Музыка</a>"
        ),
        "configuring": "<emoji document_id=6030742019024883631>📄</emoji> <b>Виджет готов и скоро будет обновлен</b>",
    }
    
    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("YandexMusicToken", None, lambda: self.strings["_cfg_yandexmusictoken"], validator=loader.validators.Hidden()),
            loader.ConfigValue("AutoBioTemplate", "🎧 {}", lambda: self.strings["_cfg_autobiotemplate"], validator=loader.validators.String()),
            loader.ConfigValue("AutoMessageTemplate", "🎧 {}", lambda: self.strings["_cfg_automesgtemplate"], validator=loader.validators.String()),
            loader.ConfigValue("update_interval", 300, lambda: self.strings["_cfg_update_interval"], validator=loader.validators.Integer(minimum=100)),
        )

    async def on_dlmod(self):
        if not self.get("guide_send", False):
            await self.inline.bot.send_message(self._tg_id, self.strings["guide"])
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
                if not self.config["YandexMusicToken"]:
                    logger.error("YandexMusicToken is missing")
                    return

                try:
                    client = ClientAsync(self.config["YandexMusicToken"])
                    await client.init()
                except Exception as e:
                    logger.error(f"Failed to initialize Yandex client: {e}")
                    return

                try:
                    track = await self.get_current_track(client)

                    if not track:
                        track = await self.get_last_liked_track(client)

                    if not track:
                        logger.info("No current or liked track found")
                        continue
                    
                    artists = ", ".join(track.artists_name())
                    title = track.title + (f" ({track.version})" if track.version else "")

                    try:
                        await self._client.edit_message(
                            *widget[:2],
                            self.config["AutoMessageTemplate"].format(f"{artists} - {title}")
                        )
                    except MessageNotModifiedError:
                        pass
                    except FloodWaitError:
                        pass
                    except Exception:
                        logger.debug("YmNow widget update failed")
                        self.set("widgets", list(set(self.get("widgets", [])) - set([widget])))
                        continue

                except Exception as e:
                    logger.error(f"Error fetching or updating track info: {e}")
                    continue

            if do_not_loop:
                break

            await asyncio.sleep(int(self.config["update_interval"]))


    async def on_unload(self):
        self._task.cancel()

    async def get_current_track(self, client):
        try:
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            return await last_track_id.fetch_track_async()
        except Exception:
            return None

    async def get_last_liked_track(self, client):
        try:
            liked_tracks = await client.users_likes_tracks()
            liked_tracks = await liked_tracks.fetch_tracks_async()
            return liked_tracks[0] if liked_tracks else None
        except Exception:
            return None

    @loader.command()
    async def automsgcmd(self, message: Message):
        """Переключить виджеты яндекс музыки."""
        state = not self.get("state", False)
        self.set("state", state)
        await utils.answer(
            message,
            self.strings["state"].format(
                "on" if state else "off", self.strings("tutorial") if state else ""
            ),
        )
    async def yafindcmd(self, message: Message):
        """Ищет трек по названию."""
        args = utils.get_args_raw(message)
    
        if not args:
            reply = await message.get_reply_message()
            if reply:
                args = reply.raw_text
            else:
                await utils.answer(message, "<emoji document_id=5843952899184398024>🚫</emoji> <b>Вы не указали название песни</b>")
                return
    
        await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji> <b>Ищу трек на Яндекс.Музыке</b>")
    
        try:
            results = await message.client.inline_query("@LyBot", args)
            await results[0].click(message.chat_id, hide_via=True)
            await message.delete()
        except Exception as e:
            if "The bot did not answer to the callback query in time" in str(e):
                await utils.answer(message, "<emoji document_id=5843952899184398024>🚫</emoji> <b>Ошибка, трека не существует.</b>")
            else:
                await utils.answer(message, f"<emoji document_id=5843952899184398024>🚫</emoji> <b>Произошла ошибка: {e}</b>")
    
    async def yanowcmd(self, message: Message):
        """Показывает что вы сейчас слушаете на яндекс музыке."""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        collecting_msg = await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji> <b>Собираю данные о том, что вы слушаете на Яндекс.Музыке</b>")

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except Exception:
            await utils.answer(message, self.strings["no_token"])
            return

        
        track = await self.get_current_track(client)

        
        if not track:
            track = await self.get_last_liked_track(client)

        if not track:
            await utils.answer(message, self.strings["my_wave"])
            return

        
        artists = ", ".join(track.artists_name())
        title = track.title + (f" ({track.version})" if track.version else "")
        playlist = track.albums[0].title if track.albums else "Нет плейлиста"

        
        try:
            lnk = track.id.split(":")[1]
        except:
            lnk = track.id
        song_link_url = f"https://song.link/ya/{lnk}"

        
        yandex_music_url = f"https://music.yandex.ru/album/{track.albums[0].id}/track/{track.id}"

        
        caption = self.strings["playing"].format(
            utils.escape_html(artists),
            utils.escape_html(title),
            utils.escape_html(playlist),
            f"{track.duration_ms // 1000 // 60:02}:{track.duration_ms // 1000 % 60:02}",
            yandex_music_url,  
            song_link_url     
        )

        try:
            info = await client.tracks_download_info(track.id, True)
            link = info[0].direct_link

            file_name = f"{artists} - {title}.mp3"
            async with aiofiles.open(file_name, 'wb') as f:
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as resp:
                        if resp.status == 200:
                            await f.write(await resp.read())

            await self.client.send_file(
                message.chat_id,
                file_name,
                caption=caption,
                voice=False,
                supports_streaming=True
            )
            await collecting_msg.delete()
            os.remove(file_name)

        except Exception as e:
            await utils.answer(message, f"<b>Ошибка получения трека: {e}</b>")


    async def yalyricscmd(self, message: Message):
        """Показывает текст песни которую вы сейчас слушаете"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        collecting_msg = await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji> <b>Собираю информацию о том, что вы слушаете на Яндекс.Музыке</b>")

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except Exception:
            await utils.answer(message, self.strings["no_token"])
            return

        track = await self.get_current_track(client)
        if not track:
            track = await self.get_last_liked_track(client)

        if not track:
            await utils.answer(message, self.strings["my_wave"])
            await collecting_msg.delete()
            return

        try:
            lyrics = await client.tracks_lyrics(track.id)
            async with aiohttp.ClientSession() as session:
                async with session.get(lyrics.download_url) as request:
                    lyric = await request.text()

            
            text = self.strings["lyrics"].format(
                utils.escape_html(', '.join(track.artists_name())),  
                utils.escape_html(track.title),                      
                utils.escape_html(lyric)                             
            )

        except Exception:
            text = self.strings["no_lyrics"]

        await utils.answer(message, text)


    async def yabiocmd(self, message: Message):
        """Переключатель показа в био трека."""
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
        """❤ Поставить лайк на трек который вы сейчас слушаете на Яндекс Музыке"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        collecting_msg = await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji> <b>Собираю информацию о том, что вы слушаете на Яндекс.Музыке</b>")

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except Exception:
            await utils.answer(message, self.strings["no_token"])
            await collecting_msg.delete()
            return

        track = await self.get_current_track(client)
        if not track:
            track = await self.get_last_liked_track(client)

        if not track:
            await utils.answer(message, self.strings["my_wave"])
            await collecting_msg.delete()
            return

        liked_tracks = await client.users_likes_tracks()
        liked_tracks = await liked_tracks.fetch_tracks_async()

        if isinstance(liked_tracks, list) and track in liked_tracks:
            await utils.answer(message, self.strings["already_liked"])
        else:
            await track.like_async()
            await utils.answer(message, self.strings["liked"])

    async def yadislikecmd(self, message: Message):
        """💔 Поставить дизлайк на трек который вы сейчас слушаете на Яндекс Музыке"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        collecting_msg = await utils.answer(message, "<emoji document_id=5463424079568584767>🎧</emoji> <b>Собираю информацию о том, что вы слушаете на Яндекс.Музыке</b>")

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except Exception:
            await utils.answer(message, self.strings["no_token"])
            await collecting_msg.delete()
            return

        track = await self.get_current_track(client)
        if not track:
            track = await self.get_last_liked_track(client)

        if not track:
            await utils.answer(message, self.strings["my_wave"])
            await collecting_msg.delete()
            return

        liked_tracks = await client.users_likes_tracks()
        liked_tracks = await liked_tracks.fetch_tracks_async()

        if isinstance(liked_tracks, list) and track in liked_tracks:
            await track.dislike_async()
            await utils.answer(message, self.strings["disliked"])
        else:
            await utils.answer(message, self.strings["not_liked"])


    @loader.loop(interval=60)
    async def autobio(self):
        if not self.config["YandexMusicToken"]:
            logger.error("YandexMusicToken is missing")
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
        except Exception as e:
            logger.error(f"Failed to initialize Yandex client: {e}")
            return

        try:
            track = await self.get_current_track(client)

            if not track:
                track = await self.get_last_liked_track(client)

            if not track:
                logger.info("No current or liked track found")
                return

            artists = ", ".join(track.artists_name())
            title = track.title + (f" ({track.version})" if track.version else "")

            text = self.config["AutoBioTemplate"].format(f"{artists} - {title}")

            try:
                await self.client(
                    UpdateProfileRequest(about=text[: 140 if self._premium else 70])
                )
            except FloodWaitError as e:
                logger.info(f"Sleeping {e.seconds} seconds due to FloodWaitError")
                await sleep(e.seconds)

        except Exception as e:
            logger.error(f"Error fetching or updating track info: {e}")

        
    async def watcher(self, message: Message):
        try:
            if "{YANDEXMUSIC}" not in getattr(message, "text", "") or not message.out:
                return

            chat_id = utils.get_chat_id(message)
            message_id = message.id

            self.set(
                "widgets",
                self.get("widgets", []) + [(chat_id, message_id, message.text)],
            )

            await utils.answer(message, self.strings["configuring"])
            await self._parse(do_not_loop=True)
        except Exception as e:
            logger.exception("Can't send widget")
            await utils.respond(message, self.strings["error"].format(e))
