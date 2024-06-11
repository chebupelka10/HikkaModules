import time
from telethon import types, events
from .. import loader, utils

@loader.tds
class ChepuxGPTBetaMod(loader.Module):
    """Позволяет разговаривать с ChatGPT без api key"""

    strings = {
        "name": "ChepuxGPT",
        "generating": "Генерирую ответ...",
        "question": "Вопрос: {}",
        "answer": "Ответ: {}",
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.command()
    async def gpt(self, message: types.Message):
        """Новая тема + задать вопрос"""
        query = utils.get_args_raw(message)
        if not query:
            await utils.answer(message, "Укажите запрос после команды .gpt")
            return

        bot_id = 7072898560

        # Загружаем сущность пользователя
        bot = await self.client.get_entity(bot_id)
        
        reset_message = await self.client.send_message(bot, "/reset")
        await reset_message.delete()

        gpt_message = await message.edit(self.strings("generating"))

        async with self.client.conversation(bot) as conv:
            await conv.send_message(query)
            response = await self._get_response(conv)
        
        await gpt_message.edit(
            "{}\n\n{}".format(
                self.strings("question").format(query),
                self.strings("answer").format(response)
            )
        )

    async def _get_response(self, conv):
        start_time = time.time()
        last_edit_time = start_time

        while True:
            msg = await conv.get_response()
            current_time = time.time()

            if (current_time - last_edit_time) > 2:
                return msg.text

            last_edit_time = current_time

            if msg.text == "Готово!":
                continue

            await msg.edit(msg.text)