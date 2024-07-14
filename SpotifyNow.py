# meta developer: @chepuxmodules
# requires: spotipy Pillow

import asyncio
import contextlib
import functools
import io
import logging
import re
import time
import traceback
from math import ceil
from types import FunctionType

import requests
import spotipy
from hikkatl.errors.rpcerrorlist import FloodWaitError
from hikkatl.tl.functions.account import UpdateProfileRequest
from hikkatl.tl.types import Message
from PIL import Image, ImageDraw, ImageFont

from .. import loader, utils

logger = logging.getLogger(__name__)
logging.getLogger("spotipy").setLevel(logging.CRITICAL)


SIZE = (1200, 320)
INNER_MARGIN = (16, 16)

TRACK_FS = 48
ARTIST_FS = 32


@loader.tds
class SpotifyMod(loader.Module):
    """Display beautiful spotify now bar. Idea: t.me/fuccsoc. Implementation: t.me/hikariatama"""

    strings = {
        "name": "SpotifyNow",
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Call"
            " </b><code>.sauth</code><b> before using this action.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Set on-repeat.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Stopped track"
            " repeat.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Skipped track.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Error occurred. Make"
            " sure the track is playing!</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You are already"
            " authentificated</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Auth successful</b>"
        ),
        "playing": "<emoji document_id=6319076999105087378>🎧</emoji> <b>Playing...</b>",
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Switched to previous"
            " track</b>"
        ),
        "paused": "<emoji document_id=5469904794376217131>🤚</emoji> <b>Pause</b>",
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Unauthentificated</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Playing track"
            " from the"
            " beginning</b>"
        ),
        "auth": (
            '<emoji document_id=5472308992514464048>🔐</emoji> <a href="{}">Proceed'
            " here</a>, approve request, then <code>.scode https://...</code> with"
            " redirected url"
        ),
        "liked": (
            "<emoji document_id=5199727145022134809>❤️</emoji> <b>Liked current"
            " playback</b>"
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Spotify autobio {}</b>"
        ),
        "404": "<emoji document_id=5312526098750252863>🚫</emoji> <b>No results</b>",
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} added to queue</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No music is"
            " playing!</b>"
        ),
        "searching": (
            "<emoji document_id=5188311512791393083>🔎</emoji> <b>Searching...</b>"
        ),
        "currently_on": "Currently listening on",
        "playlist": "Playlist",
        "owner": "Owner",
        "quality": "Quality",
    }

    strings_ru = {
        "need_auth": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Выполни"
            " </b><code>.sauth</code><b> перед выполнением этого действия.</b>"
        ),
        "on-repeat": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Повторение"
            " включено.</b>"
        ),
        "off-repeat": (
            "<emoji document_id=5472354553527541051>✋</emoji> <b>Повторение"
            " выключено.</b>"
        ),
        "skipped": (
            "<emoji document_id=5471978009449731768>👉</emoji> <b>Трек переключен.</b>"
        ),
        "err": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Произошла ошибка."
            " Убедитесь, что музыка играет!</b>\n<code>{}</code>"
        ),
        "already_authed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Уже авторизован</b>"
        ),
        "authed": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Успешная"
            " аутентификация</b>"
        ),
        "playing": "<emoji document_id=6319076999105087378>🎧</emoji> <b>Играю...</b>",
        "back": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Переключил назад</b>"
        ),
        "paused": "<emoji document_id=5469904794376217131>🤚</emoji> <b>Пауза</b>",
        "deauth": (
            "<emoji document_id=6037460928423791421>🚪</emoji> <b>Авторизация"
            " отменена</b>"
        ),
        "restarted": (
            "<emoji document_id=5469735272017043817>👈</emoji> <b>Начал трек сначала</b>"
        ),
        "liked": (
            '<emoji document_id=5310109269113186974>❤️</emoji> <b>Поставил "Мне'
            ' нравится" текущему треку</b>'
        ),
        "autobio": (
            "<emoji document_id=6319076999105087378>🎧</emoji> <b>Обновление био"
            " включено {}</b>"
        ),
        "404": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Нет результатов</b>"
        ),
        "playing_track": (
            "<emoji document_id=5212941939053175244>🎧</emoji> <b>{} добавлен в"
            " очередь</b>"
        ),
        "no_music": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Музыка не играет!</b>"
        ),
        "_cmd_doc_sfind": "Найти информацию о треке",
        "_cmd_doc_sauth": "Первый этап аутентификации",
        "_cmd_doc_scode": "Второй этап аутентификации",
        "_cmd_doc_unauth": "Отменить аутентификацию",
        "_cmd_doc_sbio": "Включить автоматическое био",
        "_cmd_doc_stokrefresh": "Принудительное обновление токена",
        "_cmd_doc_snow": "Показывает что вы слушаете на Spotify. Только для бета тестеров. Писать @chepuxcat",
        "_cls_doc": (
            "Тулкит для Spotify. Создатель @chepuxcat"
        ),
        "currently_on": "Сейчас слушаю на",
        "playlist": "Плейлист",
        "owner": "Владелец",
        "quality": "Качество",
    }


    def __init__(self):
        self._client_id = "e0708753ab60499c89ce263de9b4f57a"
        self._client_secret = "80c927166c664ee98a43a2c0e2981b4a"
        self.scope = (
            "user-read-playback-state playlist-read-private playlist-read-collaborative"
            " app-remote-control user-modify-playback-state user-library-modify"
            " user-library-read"
        )
        self.sp_auth = spotipy.oauth2.SpotifyOAuth(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri="https://thefsch.github.io/spotify/",
            scope=self.scope,
        )
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "AutoBioTemplate",
                "🎧 {} ───○ 🔊 ᴴᴰ",
                lambda: "Template for Spotify AutoBio",
            )
        )

    def create_bar(self, current_playback: dict) -> str:
        try:
            percentage = ceil(
                current_playback["progress_ms"]
                / current_playback["item"]["duration_ms"]
                * 100
            )
            bar_filled = ceil(percentage / 10) - 1
            bar_empty = 10 - bar_filled - 1
            bar = "".join("─" for _ in range(bar_filled)) + "🞆"
            bar += "".join("─" for _ in range(bar_empty))

            bar += (
                f' {current_playback["progress_ms"] // 1000 // 60:02}:{current_playback["progress_ms"] // 1000 % 60:02} /'
            )
            bar += (
                f' {current_playback["item"]["duration_ms"] // 1000 // 60:02}:{current_playback["item"]["duration_ms"] // 1000 % 60:02}'
            )
        except Exception:
            bar = "──────🞆─── 0:00 / 0:00"

        return bar

    @staticmethod
    def create_vol(vol: int) -> str:
        volume = "─" * (vol * 4 // 100)
        volume += "○"
        volume += "─" * (4 - vol * 4 // 100)
        return volume

    async def create_badge(self, thumb_url: str, title: str, artist: str) -> bytes:
        thumb = Image.open(
            io.BytesIO((await utils.run_sync(requests.get, thumb_url)).content)
        )

        im = Image.new("RGB", SIZE, (30, 30, 30))
        draw = ImageDraw.Draw(im)

        thumb_size = SIZE[1] - INNER_MARGIN[1] * 2

        thumb = thumb.resize((thumb_size, thumb_size))

        im.paste(thumb, INNER_MARGIN)

        tpos = INNER_MARGIN
        tpos = (
            tpos[0] + thumb_size + INNER_MARGIN[0] + 8,
            thumb_size // 2 - (TRACK_FS + ARTIST_FS) // 2,
        )

        draw.text(tpos, title, (255, 255, 255), font=self.font)
        draw.text(
            (tpos[0], tpos[1] + TRACK_FS + 8),
            artist,
            (180, 180, 180),
            font=self.font_smaller,
        )

        img = io.BytesIO()
        im.save(img, format="PNG")
        return img.getvalue()

    @loader.loop(interval=90)
    async def autobio(self):
        try:
            current_playback = self.sp.current_playback()
            track = current_playback["item"]["name"]
            track = re.sub(r"([(].*?[)])", "", track).strip()
        except Exception:
            return

        bio = self.config["AutoBioTemplate"].format(f"{track}")

        try:
            await self._client(
                UpdateProfileRequest(about=bio[: 140 if self._premium else 70])
            )
        except FloodWaitError as e:
            logger.info(f"Sleeping {max(e.seconds, 60)} bc of floodwait")
            await asyncio.sleep(max(e.seconds, 60))
            return

    async def _dl_font(self):
        font = (
            await utils.run_sync(
                requests.get,
                "https://github.com/hikariatama/assets/raw/master/ARIALUNI.TTF",
            )
        ).content

        self.font_smaller = ImageFont.truetype(
            io.BytesIO(font), ARTIST_FS, encoding="UTF-8"
        )
        self.font = ImageFont.truetype(io.BytesIO(font), TRACK_FS, encoding="UTF-8")
        self.font_ready.set()

    async def client_ready(self, client, db):
        self.font_ready = asyncio.Event()
        asyncio.ensure_future(self._dl_font())

        self._premium = getattr(await client.get_me(), "premium", False)
        try:
            self.sp = spotipy.Spotify(auth=self.get("acs_tkn")["access_token"])
        except Exception:
            self.set("acs_tkn", None)
            self.sp = None

        if self.get("autobio", False):
            self.autobio.start()

        with contextlib.suppress(Exception):
            await utils.dnd(client, "@DirectLinkGenerator_Bot", archive=True)

        self.musicdl = await self.import_lib(
            "https://libs.hikariatama.ru/musicdl.py",
            suspend_on_error=True,
        )

    def tokenized(func) -> FunctionType:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if not args[0].get("acs_tkn", False) or not args[0].sp:
                await utils.answer(args[1], args[0].strings("need_auth"))
                return

            return await func(*args, **kwargs)

        wrapped.__doc__ = func.__doc__
        wrapped.__module__ = func.__module__

        return wrapped

    def error_handler(func) -> FunctionType:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception:
                logger.exception(traceback.format_exc())
                with contextlib.suppress(Exception):
                    await utils.answer(
                        args[1],
                        args[0].strings("err").format(traceback.format_exc()),
                    )

        wrapped.__doc__ = func.__doc__
        wrapped.__module__ = func.__module__

        return wrapped

    def autodelete(func) -> FunctionType:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            a = await func(*args, **kwargs)
            with contextlib.suppress(Exception):
                await asyncio.sleep(10)
                await args[1].delete()

            return a

        wrapped.__doc__ = func.__doc__
        wrapped.__module__ = func.__module__

        return wrapped

    @error_handler
    @tokenized
    @autodelete
    async def srepeatcmd(self, message: Message):
        """💫 Повторять трек"""
        self.sp.repeat("track")
        await utils.answer(message, self.strings("on-repeat"))

    @error_handler
    @tokenized
    @autodelete
    async def sderepeatcmd(self, message: Message):
        """✋ Перестать повторять трек"""
        self.sp.repeat("context")
        await utils.answer(message, self.strings("off-repeat"))

    @error_handler
    @tokenized
    @autodelete
    async def snextcmd(self, message: Message):
        """👉 Следующий трек"""
        self.sp.next_track()
        await utils.answer(message, self.strings("skipped"))

    @error_handler
    @tokenized
    @autodelete
    async def spausecmd(self, message: Message):
        """🤚 Пауза"""
        self.sp.pause_playback()
        await utils.answer(message, self.strings("paused"))

    @error_handler
    @tokenized
    @autodelete
    async def splaycmd(self, message: Message, from_sq: bool = False):
        """▶️ Продолжить играть"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not args:
            if not reply or "https://open.spotify.com/track/" not in reply.text:
                self.sp.start_playback()
                await utils.answer(message, self.strings("playing"))
                return
            else:
                args = re.search('https://open.spotify.com/track/(.+?)"', reply.text)[1]

        try:
            track = self.sp.track(args)
        except Exception:
            search = self.sp.search(q=args, type="track", limit=1)
            if not search:
                await utils.answer(message, self.strings("404"))
            try:
                track = search["tracks"]["items"][0]
            except Exception:
                await utils.answer(message, self.strings("404"))
                return

        self.sp.add_to_queue(track["id"])

        if not from_sq:
            self.sp.next_track()

        await message.delete()
        await self._client.send_file(
            message.peer_id,
            await self.create_badge(
                track["album"]["images"][0]["url"],
                track["name"],
                ", ".join([_["name"] for _ in track["artists"]]),
            ),
            caption=self.strings("playing_track").format(track["name"]),
        )

    @error_handler
    @tokenized
    @autodelete
    async def sfindcmd(self, message: Message):
        """Ищет информацию о треке"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("404"))

        message = await utils.answer(message, self.strings("searching"))

        try:
            track = self.sp.track(args)
        except Exception:
            search = self.sp.search(q=args, type="track", limit=1)
            if not search:
                await utils.answer(message, self.strings("404"))
            try:
                track = search["tracks"]["items"][0]
                assert track
            except Exception:
                await utils.answer(message, self.strings("404"))
                return

        await self._open_track(track, message)

    async def _open_track(
        self,
        track: dict,
        message: Message,
        override_text: str = None,
    ):
        name = track.get("name")
        artists = [
            artist["name"] for artist in track.get("artists", []) if "name" in artist
        ]

        full_song_name = f"{name} - {', '.join(artists)}"

        music = await self.musicdl.dl(full_song_name, only_document=True)

        await self._client.send_file(
            message.peer_id,
            music,
            caption=(
                override_text
                or (
                    (
                        f"🗽 <b>{utils.escape_html(full_song_name)}</b>{{is_flac}}"
                        if artists
                        else f"🗽 <b>{utils.escape_html(track)}</b>{{is_flac}}"
                    )
                    if track
                    else "{is_flac}"
                )
            ).format(
                is_flac=(
                    "\n<emoji document_id=5359582743992737342>😎</emoji> <b>FLAC"
                    f" {self.strings('quality')}</b>"
                    if getattr(music, "is_flac", False)
                    else ""
                )
            ),
        )

        if message.out:
            await message.delete()

    @error_handler
    @tokenized
    async def sqcmd(self, message: Message):
        """🔎 Поиск песен"""
        await self.splaycmd(message, True)

    @error_handler
    @tokenized
    @autodelete
    async def sbackcmd(self, message: Message):
        """⏮ Предыдущий трек"""
        self.sp.previous_track()
        await utils.answer(message, self.strings("back"))

    @error_handler
    @tokenized
    @autodelete
    async def sbegincmd(self, message: Message):
        """⏪ Трек заного"""
        self.sp.seek_track(0)
        await utils.answer(message, self.strings("restarted"))

    @error_handler
    @tokenized
    @autodelete
    async def slikecmd(self, message: Message):
        """❤️ Поставить лайк на трек"""
        cupl = self.sp.current_playback()
        self.sp.current_user_saved_tracks_add([cupl["item"]["id"]])
        await utils.answer(message, self.strings("liked"))

    @error_handler
    async def sauthcmd(self, message: Message):
        """First stage of auth"""
        if self.get("acs_tkn", False) and not self.sp:
            await utils.answer(message, self.strings("already_authed"))
        else:
            self.sp_auth.get_authorize_url()
            await utils.answer(
                message,
                self.strings("auth").format(self.sp_auth.get_authorize_url()),
            )

    @error_handler
    @autodelete
    async def scodecmd(self, message: Message):
        """Second stage of auth"""
        url = message.message.split(" ")[1]
        code = self.sp_auth.parse_auth_response_url(url)
        self.set("acs_tkn", self.sp_auth.get_access_token(code, True, False))
        self.sp = spotipy.Spotify(auth=self.get("acs_tkn")["access_token"])
        await utils.answer(message, self.strings("authed"))

    @error_handler
    @autodelete
    async def unauthcmd(self, message: Message):
        """Deauth from Spotify API"""
        self.set("acs_tkn", None)
        del self.sp
        await utils.answer(message, self.strings("deauth"))

    @error_handler
    @tokenized
    @autodelete
    async def sbiocmd(self, message: Message):
        """Toggle bio playback streaming"""
        current = self.get("autobio", False)
        new = not current
        self.set("autobio", new)
        await utils.answer(
            message,
            self.strings("autobio").format("enabled" if new else "disabled"),
        )

        if new:
            self.autobio.start()
        else:
            self.autobio.stop()

    @error_handler
    @tokenized
    @autodelete
    async def stokrefreshcmd(self, message: Message):
        """Force refresh token"""
        self.set(
            "acs_tkn",
            self.sp_auth.refresh_access_token(self.get("acs_tkn")["refresh_token"]),
        )
        self.set("NextRefresh", time.time() + 45 * 60)
        self.sp = spotipy.Spotify(auth=self.get("acs_tkn")["access_token"])
        await utils.answer(message, self.strings("authed"))

    @error_handler
    async def snowcmd(self, message):
        """Показывает что вы слушаете на Spotify. Только для бета тестеров. Писать @chepuxcat"""
        await utils.answer(message, "<emoji document_id=5348240937954851856>🎧</emoji> <b>Собираю данные о том, что вы слушаете на Spotify</b>")
        try:
            results = await message.client.inline_query("@properdeezbot", "...")
            await results[0].click(message.chat_id, hide_via=True)
            await message.delete()
        except Exception as e:
            if "The bot did not answer to the callback query in time" in str(e):
                await utils.answer(message, "<emoji document_id=5312526098750252863>❌</emoji><b>Ошибка, вы не слушаете трек, или не сделали инструкцию которая есть в инструкции команды. (Посмотрите help spotifyow)</b>")
            else:
                await utils.answer(message, f"<emoji document_id=5312526098750252863>❌</emoji><b>Произошла ошибка: {e}</b>")

    @error_handler
    async def snowtrackcmd(self, message):
        """Показывает что вы слушаете на Spotify и отправляет его треком. Только для бета тестеров. Писать @chepuxcat"""
        await utils.answer(message, "<emoji document_id=5348240937954851856>🎧</emoji> <b>Собираю данные о том, что вы слушаете на Spotify</b>")
        try:
            results = await message.client.inline_query("@properdeezbot", "")
            await results[0].click(message.chat_id, hide_via=True)
            await message.delete()
        except Exception as e:
            if "The bot did not answer to the callback query in time" in str(e):
                await utils.answer(message, "<emoji document_id=5312526098750252863>❌</emoji><b>Ошибка, вы не слушаете трек, или не сделали инструкцию которая есть в инструкции команды. (Посмотрите help spotifyow)</b>")
            else:
                await utils.answer(message, f"<emoji document_id=5312526098750252863>❌</emoji><b>Произошла ошибка: {e}</b>")


    async def watcher(self, message: Message):
        """Watcher is used to update token"""
        if not self.sp:
            return

        if self.get("NextRefresh", False):
            ttc = self.get("NextRefresh", 0)
            crnt = time.time()
            if ttc < crnt:
                self.set(
                    "acs_tkn",
                    self.sp_auth.refresh_access_token(
                        self.get("acs_tkn")["refresh_token"]
                    ),
                )
                self.set("NextRefresh", time.time() + 45 * 60)
                self.sp = spotipy.Spotify(auth=self.get("acs_tkn")["access_token"])
        else:
            self.set(
                "acs_tkn",
                self.sp_auth.refresh_access_token(self.get("acs_tkn")["refresh_token"]),
            )
            self.set("NextRefresh", time.time() + 45 * 60)
            self.sp = spotipy.Spotify(auth=self.get("acs_tkn")["access_token"])

    async def on_unload(self):
        with contextlib.suppress(Exception):
            self.autobio.stop()
