# -*- coding: utf-8 -*-

from .. import loader, utils
import asyncio
import logging

logger = logging.getLogger(__name__)

def register(cb):
    cb(AutoRestartMod())

class AutoRestartMod(loader.Module):
    """Автоматический перезапуск бота и сервера"""
    strings = {"name": "AutoRestart"}

    def __init__(self):
        self.name = self.strings["name"]
        self._me = None
        self._ratelimit = []
        self.restart_task = None
        self.lrestart_task = None

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()
        self.restart_task = asyncio.create_task(self.auto_restart())
        self.lrestart_task = asyncio.create_task(self.auto_lrestart())

    async def autorestartcmd(self, message):
        """Установить интервал перезапуска бота в часах. Используйте 0 для отключения."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Укажите интервал в часах</b>")
            return
        try:
            hours = float(args)
            if hours < 0:
                raise ValueError
        except ValueError:
            await utils.answer(message, "<b><emoji document_id=5312526098750252863>❌</emoji> Неверный формат интервала</b>")
            return
        self._db.set(__name__, "restart_interval", hours)
        await utils.answer(message, f"<b><emoji document_id=5314250708508220914>✅</emoji> Интервал перезапуска бота установлен на {hours} часов</b>")

    async def autolrestartcmd(self, message):
        """Установить интервал перезапуска lavhost в часах. Используйте 0 для отключения.(Необходимо скачать модуль https://heta.hikariatama.ru/iamnalinor/FTG-modules/lavhost.py)"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Укажите интервал в часах</b>")
            return
        try:
            hours = float(args)
            if hours < 0:
                raise ValueError
        except ValueError:
            await utils.answer(message, " <b><emoji document_id=5312526098750252863>❌</emoji> Неверный формат интервала</b>")
            return
        self._db.set(__name__, "lrestart_interval", hours)
        await utils.answer(message, f"<b> <emoji document_id=5314250708508220914>✅</emoji> Интервал перезапуска сервера установлен на {hours} часов</b>")

    async def auto_restart(self):
        while True:
            interval = self._db.get(__name__, "restart_interval", 0)
            if interval > 0:
                await asyncio.sleep(interval * 3600)
                logger.info("Restarting bot")
                await self._client.send_message("me", ".restart")
            else:
                await asyncio.sleep(1)

    async def auto_lrestart(self):
        while True:
            interval = self._db.get(__name__, "lrestart_interval", 0)
            if interval > 0:
                await asyncio.sleep(interval * 3600)
                logger.info("Restarting server")
                await self._client.send_message("me", ".lrestart")
            else:
                await asyncio.sleep(1)
