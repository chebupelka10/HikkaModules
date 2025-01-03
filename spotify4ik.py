# meta developer: @MiSidePlayer

import os
import asyncio
import logging
import tempfile
import aiohttp

import yt_dlp
import spotipy

from telethon import types
from telethon.tl.functions.account import UpdateProfileRequest

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class Spotify4ik(loader.Module):
    """Слушай музыку в Spotify. Updated by @MiSidePlayer. Original module creator @FAmods"""

    strings = {
        "name": "Spotify4ik",

        "go_auth_link": """<b><emoji document_id=5271604874419647061>🔗</emoji> Ссылка для авторизации создана!
        
🔐 Перейди по <a href='{}'>этой ссылке</a>.
        
✏️ Потом введи: <code>{}scode полученная_ссылка</code></b>""",

        "no_auth_token": "<emoji document_id=5854929766146118183>❌</emoji> <b>Авторизуйся в свой аккаунт через <code>{}sauth</code></b>",
        "no_song_playing": "<emoji document_id=5854929766146118183>❌</emoji> <b>Сейчас ничего не играет.</b>",
        "no_code": "<emoji document_id=5854929766146118183>❌</emoji> <b>Должно быть <code>{}scode полученная ссылка</code></b>",
        "code_installed": """<b><emoji document_id=5330115548900501467>🔑</emoji> Код авторизации установлен!</b>
        
<emoji document_id=5870794890006237381>🎶</emoji> <b>Наслаждайся музыкой!</b>""",

        "auth_error": "<emoji document_id=5854929766146118183>❌</emoji> <b>Ошибка авторизации:</b> <code>{}</code>",
        "unexpected_error": "<emoji document_id=5854929766146118183>❌</emoji> <b>Произошла ошибка:</b> <code>{}</code>",

        "track_pause": "<b><emoji document_id=6334755820168808080>⏸️</emoji> Трек поставлен на паузу.</b>",
        "track_play": "<b><emoji document_id=5188621441926438751>🎵</emoji> Играю...</b>",

        "track_loading": "<emoji document_id=5294137402430858861>🎵</emoji> <b>Скачиваем трек, почти готово!</b>",

        "music_bio_disabled": "<b><emoji document_id=5334673106202010226>✏️</emoji> Стрим музыки в био выключен</b>",
        "music_bio_enabled": "<b><emoji document_id=5334673106202010226>✏️</emoji> Стрим музыки в био включен</b>",

        "track_skipped": "<b><emoji document_id=5188621441926438751>🎵</emoji> Следующий трек...</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "auth_token",
                None,
                lambda: "Токен для авторизации",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "bio_text",
                "🎵 {track_name} - {artist_name}",
                lambda: "Текст био с текущим треком",
            ),
        )
        self.sp = None
        self.sp_auth = spotipy.oauth2.SpotifyOAuth(
            client_id="e0708753ab60499c89ce263de9b4f57a",
            client_secret="80c927166c664ee98a43a2c0e2981b4a",
            redirect_uri="https://thefsch.github.io/spotify/",
            scope=(
                "user-read-playback-state playlist-read-private playlist-read-collaborative "
                "app-remote-control user-modify-playback-state user-library-modify user-library-read"
            ),
        )
        self.auth_token = None
        self.refresh_token = None
        self._bio_task = None

async def client_ready(self, client, db):
    self.db = db
    self._client = client
    self.auth_token = self.config["auth_token"]

    if not self.auth_token:
        logger.warning("Auth token is missing. Spotify functionality may not work correctly.")

    if self.db.get(self.name, "bio_change", False):
        self._bio_task = asyncio.create_task(self._update_bio())

    self._token_refresh_task = asyncio.create_task(self.refresh_auth_token())


    async def _update_bio(self):
        while True:
            try:
                if not self.db.get(self.name, "bio_change", False):
                    break

                self.auth_token = self.config["auth_token"]
                sp = spotipy.Spotify(auth=self.auth_token)
                current_playback = sp.current_playback()

                if current_playback and current_playback.get("item"):
                    track = current_playback["item"]
                    track_name = track.get("name", "Unknown Track")
                    artist_name = track["artists"][0].get("name", "Unknown Artist")
                    bio = self.config["bio_text"].format(track_name=track_name, artist_name=artist_name)

                    premium = getattr(await self._client.get_me(), "premium", False)
                    await self._client(UpdateProfileRequest(about=bio[:140 if premium else 70]))
            except Exception as e:
                logger.error(f"Error updating bio: {e}")

            await asyncio.sleep(90)

    @loader.command()
    async def sauth(self, message):
        """Получить ссылку для входа в аккаунт"""
        auth_url = self.sp_auth.get_authorize_url()
        await utils.answer(message, self.strings['go_auth_link'].format(auth_url, self.get_prefix()))

    @loader.command()
    async def scode(self, message):
        """Ввести код авторизации"""
        code = utils.get_args_raw(message)
        if not code:
            return await utils.answer(message, self.strings['no_code'].format(self.get_prefix()))

        if code.startswith("https://thefsch.github.io/spotify/?code="):
            code = code.replace("https://thefsch.github.io/spotify/?code=", "")

        try:
            token_info = self.sp_auth.get_access_token(code)
            self.auth_token = token_info.get('access_token')
            self.refresh_token = token_info.get('refresh_token')

            if not self.auth_token or not self.refresh_token:
                raise ValueError("Access or refresh token is missing")

            self.sp = spotipy.Spotify(auth=self.auth_token)

            self.config["auth_token"] = self.auth_token

            await utils.answer(message, self.strings['code_installed'])
        except Exception as e:
            logger.error("Authorization error", exc_info=True)
            await utils.answer(message, self.strings['auth_error'].format(str(e)))

    @loader.command()
    async def spause(self, message):
        """⏸️ Поставить на паузу текущий трек"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        sp = spotipy.Spotify(auth=self.config['auth_token'])

        try:
            sp.pause_playback()
        except spotipy.oauth2.SpotifyOauthError as e:
            return await utils.answer(message, self.strings['auth_error'].format(str(e)))
        except spotipy.exceptions.SpotifyException as e:
            if "Restriction violated" in str(e):
                return await utils.answer(message, self.strings['track_pause'])
            if "The access token expired" in str(e):
                return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))
            if "NO_ACTIVE_DEVICE" in str(e):
                return await utils.answer(message, self.strings['no_song_playing'])
            return await utils.answer(message, self.strings['unexpected_error'].format(str(e)))
        await utils.answer(message, self.strings['track_pause'])

    @loader.command()
    async def splay(self, message):
        """🎶 Воспроизвести текущий трек"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        sp = spotipy.Spotify(auth=self.config['auth_token'])

        try:
            sp.start_playback()
        except spotipy.oauth2.SpotifyOauthError as e:
            return await utils.answer(message, self.strings['auth_error'].format(str(e)))
        except spotipy.exceptions.SpotifyException as e:
            if "Restriction violated" in str(e):
                return await utils.answer(message, self.strings['track_play'])
            if "The access token expired" in str(e):
                return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))
            if "NO_ACTIVE_DEVICE" in str(e):
                return await utils.answer(message, self.strings['no_song_playing'])
            return await utils.answer(message, self.strings['unexpected_error'].format(str(e)))
        await utils.answer(message, self.strings['track_play'])
        
    @loader.command()
    async def slike(self, message):
        """❤️ Добавить текущий трек в избранное"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        try:
            sp = spotipy.Spotify(auth=self.config['auth_token'])
            current_playback = sp.current_playback()

            if not current_playback or not current_playback.get('item'):
                return await utils.answer(message, self.strings['no_song_playing'])

            track = current_playback['item']
            track_id = track.get('id')

            if not track_id:
                return await utils.answer(message, self.strings['unexpected_error'].format("Не удалось получить ID трека."))

            sp.current_user_saved_tracks_add([track_id])

            track_name = track.get('name', 'Unknown Track')
            artist_name = track['artists'][0].get('name', 'Unknown Artist')

            await utils.answer(
                message,
                f"<b><emoji document_id=5872863028428410654>❤️</emoji> Трек <code>{track_name}</code> - <code>{artist_name}</code> добавлен в избранное!</b>"
            )

        except spotipy.SpotifyException as e:
            await utils.answer(message, self.strings['auth_error'].format(e))

        except Exception as e:
            await utils.answer(message, self.strings['unexpected_error'].format(e))


    @loader.command()
    async def snext(self, message):
        """➡️ Включить следующий трек"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        sp = spotipy.Spotify(auth=self.config['auth_token'])

        try:
            sp.next_track()
        except spotipy.oauth2.SpotifyOauthError as e:
            return await utils.answer(message, self.strings['auth_error'].format(str(e)))
        except spotipy.exceptions.SpotifyException as e:
            if "Restriction violated" in str(e):
                return await utils.answer(message, self.strings['track_play'])
            if "The access token expired" in str(e):
                return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))
            if "NO_ACTIVE_DEVICE" in str(e):
                return await utils.answer(message, self.strings['no_song_playing'])
                return await utils.answer(message, self.strings['unexpected_error'].format(str(e)))
        await utils.answer(message, self.strings['track_skipped'])
     
    @loader.command()
    async def sback(self, message):
        """⏮ Вернуться к предыдущему треку"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        try:
            sp = spotipy.Spotify(auth=self.config['auth_token'])
            sp.previous_track()
            await utils.answer(message, "<b><emoji document_id=5352759161945867747>🔙</emoji> Переключено на предыдущий трек!</b>")

        except spotipy.SpotifyException as e:
            await utils.answer(message, self.strings['auth_error'].format(e))

        except Exception as e:
            await utils.answer(message, self.strings['unexpected_error'].format(e))


    @loader.command()
    async def sbegin(self, message):
        """⏪ Включить текущий трек с начала"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        try:
            sp = spotipy.Spotify(auth=self.config['auth_token'])
            current_playback = sp.current_playback()

            if not current_playback or not current_playback.get('item'):
                return await utils.answer(message, self.strings['no_song_playing'])

            sp.seek_track(0)
            await utils.answer(message, "<b><emoji document_id=5451646226975955576>⌛️</emoji> Трек начат с начала!</b>")

        except spotipy.SpotifyException as e:
            await utils.answer(message, self.strings['auth_error'].format(e))

        except Exception as e:
            await utils.answer(message, self.strings['unexpected_error'].format(e))
    @loader.command()
    async def sbio(self, message):
        """✏️ Включить/выключить стрим текущего трека в био"""
        self.auth_token = self.config["auth_token"]
        if not self.auth_token:
            return await utils.answer(message, self.strings["no_auth_token"].format(self.get_prefix()))

        if self.db.get(self.name, "bio_change", False):
            self.db.set(self.name, "bio_change", False)
            if self._bio_task:
                self._bio_task.cancel()
                self._bio_task = None
            return await utils.answer(message, self.strings["music_bio_disabled"])

        self.db.set(self.name, "bio_change", True)
        self._bio_task = asyncio.create_task(self._update_bio())
        await utils.answer(message, self.strings["music_bio_enabled"])
        
    @loader.command()
    async def snow(self, message):
        """🎧 Показывает что вы слушаете на Spotify"""
        self.config['auth_token'] = self.auth_token
        if not self.config['auth_token']:
            return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))

        try:
            sp = spotipy.Spotify(auth=self.config['auth_token'])
            current_playback = sp.current_playback()

            if not current_playback or not current_playback.get('item'):
                return await utils.answer(message, self.strings['no_song_playing'])

            await utils.answer(message, self.strings['track_loading'])

            track = current_playback['item']
            track_name = track.get('name', 'Unknown Track')
            artist_name = track['artists'][0].get('name', 'Unknown Artist')
            album_name = track['album'].get('name', 'Unknown Album')
            duration_ms = track.get('duration_ms', 0)
            progress_ms = current_playback.get('progress_ms', 0)
            is_playing = current_playback.get('is_playing', False)

            duration_min, duration_sec = divmod(duration_ms // 1000, 60)
            progress_min, progress_sec = divmod(progress_ms // 1000, 60)

            playlist = current_playback.get('context', {}).get('uri', '').split(':')[-1] if current_playback.get('context') else None
            device_name = current_playback.get('device', {}).get('name', 'Unknown Device')+" "+current_playback.get('device', {}).get('type', '')
            device_type = current_playback.get('device', {}).get('type', 'unknown')

            user_profile = sp.current_user()
            user_name = user_profile['display_name']
            user_id = user_profile['id']

            track_url = track['external_urls']['spotify']
            user_url = f"https://open.spotify.com/user/{user_id}"
            playlist_url = f"https://open.spotify.com/playlist/{playlist}" if playlist else None

            track_info = (
                f"<b><emoji document_id=5188705588925702510>🎶</emoji> {track_name} - <code>{artist_name}</code>\n"
                f"<b><emoji document_id=5870794890006237381>💿</emoji> Album:</b> <code>{album_name}</code>\n\n"
                f"<b><emoji document_id=6007938409857815902>🎧</emoji> Device:</b> <code>{device_name}</code>\n"
                + (("<b><emoji document_id=5872863028428410654>❤️</emoji> From favorite tracks</b>\n" if "playlist/collection" in playlist_url else
                    f"<b><emoji document_id=5944809881029578897>📑</emoji> From Playlist:</b> <a href='{playlist_url}'>View</a>\n") if playlist else "")
                + f"\n<b><emoji document_id=5902449142575141204>🔗</emoji> Track URL:</b> <a href='{track_url}'>Open in Spotify</a>"
            )
            with tempfile.TemporaryDirectory() as temp_dir:
                audio_path = os.path.join(temp_dir, f"{artist_name} - {track_name}.mp3")
                ydl_opts = {
                    "format": "bestaudio/best[ext=mp3]",
                    "outtmpl": audio_path,
                    "noplaylist": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"ytsearch1:{track_name} - {artist_name}"])

                album_art_url = track['album']['images'][0]['url']
                async with aiohttp.ClientSession() as session:
                    async with session.get(album_art_url) as response:
                        art_path = os.path.join(temp_dir, "cover.jpg")
                        with open(art_path, "wb") as f:
                            f.write(await response.read())

                await self._client.send_file(
                    message.chat_id,
                    audio_path,
                    caption=track_info,
                    attributes=[
                        types.DocumentAttributeAudio(
                            duration=duration_ms//1000,
                            title=track_name,
                            performer=artist_name
                        )
                    ],
                    thumb=art_path,
                    reply_to=message.reply_to_msg_id if message.is_reply else getattr(message, "top_id", None)
                )

            await message.delete()

        except spotipy.oauth2.SpotifyOauthError as e:
            return await utils.answer(message, self.strings['auth_error'].format(str(e)))
        except spotipy.exceptions.SpotifyException as e:
            if "The access token expired" in str(e):
                return await utils.answer(message, self.strings['no_auth_token'].format(self.get_prefix()))
            if "NO_ACTIVE_DEVICE" in str(e):
                return await utils.answer(message, self.strings['no_song_playing'])
            return await utils.answer(message, self.strings['unexpected_error'].format(str(e)))

async def refresh_auth_token(self):
    while not self.auth_token:
        logger.warning("Auth token is missing. Waiting for 1 minute before retrying.")
        await asyncio.sleep(60)

    while True:
        try:
            logger.info("Refreshing Spotify token in loop...")
            token_info = self.sp_auth.refresh_access_token(self.auth_token)
            self.auth_token = token_info.get('access_token')

            if not self.auth_token:
                logger.error("Failed to refresh token: No access token returned")
                await asyncio.sleep(60)
                continue

            self.sp = spotipy.Spotify(auth=self.auth_token)
            logger.info("Spotify token refreshed successfully")
            await asyncio.sleep(45 * 60)

        except Exception as e:
            logger.error("Failed to refresh Spotify token", exc_info=True)
            await asyncio.sleep(60)
