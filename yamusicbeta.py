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
    strings = {
        "no_token": "<b>Specify a token in config!</b>",
        "playing": "<b>Now playing:</b> <code>{}</code><b> - </b><code>{}</code>\n<b>{}</b>",
        "no_args": "<b>Provide arguments!</b>",
        "state": "<b>Widgets are now {}</b>\n{}",
        "tutorial": "<b>To enable widget, send a message to a preffered chat with text</b> <code>{YANDEXMUSIC}</code>",
        "no_results": "<b>No results found :(</b>",
        "autobioe": "<b>Autobio enabled</b>",
        "autobiod": "<b>Autobio disabled</b>",
        "lyrics": "<b>Lyrics: \n{}</b>",
        "already_liked": "<b>Current playing track is already liked!</b>",
        "liked": "<b>Liked current playing track!</b>",
        "not_liked": "<b>Current playing track not liked!</b>",
        "disliked": "<b>Disliked current playing track!</b>",
        "my_wave": "<b>You listening to track in my wave, i can't recognize it.</b>",
        "no_lyrics": "<b>Track doesn't have lyrics.</b>",
        "guide": '<a href="https://github.com/MarshalX/yandex-music-api/discussions/513#discussioncomment-2729781">Instructions for obtaining a Yandex.Music token</a>',
        "configuring": "<b>Widget is ready and will be updated soon</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("YandexMusicToken", None, "Yandex.Music account token"),
            loader.ConfigValue("AutoBioTemplate", "🎧 {}", "Template for AutoBio"),
            loader.ConfigValue("AutoMessageTemplate", "🎧 {}", "Template for AutoMessage"),
            loader.ConfigValue("update_interval", 300, "Update interval"),
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

    async def on_unload(self):
        self._task.cancel()

    @loader.command()
    async def ynowcmd(self, message: Message):
        """Get now playing track"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
            info = await client.tracks_download_info(last_track.id, True)
            link = info[0].direct_link
            artists = ", ".join(last_track.artists_name())
            title = last_track.title
            if last_track.version:
                title += f" ({last_track.version})"
            lnk = last_track.id.split(":")[1] if ":" in last_track.id else last_track.id
            caption = self.strings["playing"].format(
                utils.escape_html(artists),
                utils.escape_html(title),
                f"{last_track.duration_ms // 1000 // 60:02}:{last_track.duration_ms // 1000 % 60:02}",
            )
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
        except:
            await utils.answer(message, self.strings["my_wave"])

    @loader.command()
    async def ylyrics(self, message: Message):
        """Get now playing track lyrics"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
            lyrics = await client.tracks_lyrics(last_track.id)
            async with aiohttp.ClientSession() as session:
                async with session.get(lyrics.download_url) as request:
                    lyric = await request.text()
            text = self.strings["lyrics"].format(utils.escape_html(lyric))
        except:
            text = self.strings["no_lyrics"]

        await utils.answer(message, text)

    @loader.command()
    async def ybio(self, message: Message):
        """Show now playing track in your bio"""
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

    async def ylikecmd(self, message: Message):
        """❤ Like now playing track"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
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
        except:
            await utils.answer(message, self.strings["my_wave"])

    async def ydislikecmd(self, message: Message):
        """💔 Dislike now playing track"""
        if not self.config["YandexMusicToken"]:
            await utils.answer(message, self.strings["no_token"])
            return

        try:
            client = ClientAsync(self.config["YandexMusicToken"])
            await client.init()
            queues = await client.queues_list()
            last_queue = await client.queue(queues[0].id)
            last_track_id = last_queue.get_current_track()
            last_track = await last_track_id.fetch_track_async()
            liked_tracks = await client.users_likes_tracks()
            liked_tracks = await liked_tracks.fetch_tracks_async()
            if isinstance(liked_tracks, list):
                if last_track in liked_tracks:
                    await last_track.dislike_async()
                    await utils.answer(message, self.strings["disliked"])
                else:
                    await utils.answer(message, self.strings["not_liked"])
            else:
                await utils.answer(message, self.strings["not_liked"])
        except:
            await utils.answer(message, self.strings["my_wave"])
