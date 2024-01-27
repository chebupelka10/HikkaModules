# meta developer: @chepuxmodules

from .. import loader, utils
import asyncio
import time


class AutoRestartMod(loader.Module):
    """Перезагружайте автоматически ваш юзербот by @y9chebupelka"""
    
    strings = {"name": "AutoRestart",
               "config_error": "<b><emoji document_id=5314591660192046611>❌</emoji> Неверное значение в конфиге. Пожалуйста, установите положительное число часов.</b>",
               "status_on": "<b><emoji document_id=5308041633202182757>✔️</emoji> Автоматический перезапуск включен. Бот будет перезапускаться каждые {} часов.</b>",
               "status_off": "<b><emoji document_id=5314591660192046611>❌</emoji> Автоматический перезапуск выключен.</b>",
               "restart_message": ".restart -f"}

    
    def __init__(self):
        
        self.config = loader.ModuleConfig("HOURS", 0, lambda m: self.strings["name"])
        
        self.task = None

    
    @loader.owner
    async def autolrestartcmd(self, message):
        """Проверить статус перезагрузки юзербота"""
        
        hours = self.config["HOURS"]
        
        if hours > 0:
            
            await utils.answer(message, self.strings["status_on"].format(hours))
        else:
            
            await utils.answer(message, self.strings["status_off"])

    
    async def client_ready(self, client, db):
        
        hours = self.config["HOURS"]
        
        if hours > 0:
            
            self.task = asyncio.create_task(self.restart_loop(client, hours))
        else:
            if self.task:
                self.task.cancel()
                self.task = None

    async def client_disconnect(self, client):
        if self.task:
            self.task.cancel()
            self.task = None

    async def restart_loop(self, client, hours):
        while True:
            await asyncio.sleep(hours * 3600)
            await client.send_message(2055270939, self.strings["restart_message"])
