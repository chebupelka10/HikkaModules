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
    Module for Yandex Music. Based on SpotifyNow, YaNow, and WakaTime. [BETA]
    """

    strings = {
        "name": "YmNow",
        "no_token": "<b>🚫 Specify a token in config!</b>",
        "playing": "<b>🎶 Now playing:</b> <code>{}</code><b> - </b><code>{}</code>\n<b>🕐 {}</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "YandexMusicToken",
                None,
                lambda: self.strings["no_token"],
                validator=loader.validators.String(),
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

        self.set("widgets", list(map(tuple, self.get("widgets", []))))

        self._task = asyncio.ensure_future(self._parse())

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

        # Sending message with photo and link
        await self.inline.form(
            message=message,
            text=caption,
            reply_markup={
                "text": "song.link",
                "url": f"https://song.link/ya/{lnk}",
            },
            silent=True,
            audio={
                "title": utils.escape_html(title),
                "performer": utils.escape_html(artists),
            },
        )

    @loader.command()
    async def yanowtrack(self, message: Message):
        """Get now playing track without sending photo"""

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

        artists = ", ".join(last_track.artists_name())
        title = last_track.title
        if last_track.version:
            title += f" ({last_track.version})"
        else:
            pass

        # Sending text message with track information
        await utils.answer(
            message,
            self.strings["playing"].format(
                utils.escape_html(artists),
                utils.escape_html(title),
                f"{last_track.duration_ms // 1000 // 60:02}:{last_track.duration_ms // 1000 % 60:02}",
            ),
        )
