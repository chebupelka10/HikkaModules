import time
from telethon import types, events, utils
from .. import loader

@loader.tds
class ChepuxGPTBetaMod(loader.Module):
    """Позволяет разговаривать с ChatGPT без api key"""

    strings = {
        "name": "ChepuxGPT",
        "generating": "Генерирую ответ...",
        "question": "Вопрос: {}",
        "answer": "Ответ: {}",
        "wait": "Подождите, идет генерация ответа на предыдущий запрос."
    }

    generating_response = False

    async def client_ready(self, client, db):
        self.client = client

    @loader.command()
    async def gptcmd(self, message: types.Message):
        """Новая тема + задать вопрос"""
        if self.generating_response:
            await utils.answer(message, self.strings["wait"])
            return

        query = utils.get_args_raw(message)
        if not query:
            await utils.answer(message, "Укажите запрос после команды .gptcmd")
            return

        self.generating_response = True
        bot_id = 7072898560  # ID бота

        try:
            # Загружаем сущность пользователя
            bot = await self.client.get_entity(bot_id)

            reset_message = await self.client.send_message(bot, "/reset")
            await reset_message.delete()

            gpt_message = await message.edit(self.strings["generating"])

            async with self.client.conversation(bot) as conv:
                await conv.send_message(query)
                response = await self._get_response(conv)

            await gpt_message.edit(
                "{}\n\n{}".format(
                    self.strings["question"].format(query),
                    self.strings["answer"].format(response)
                )
            )
        finally:
            self.generating_response = False

    async def _get_response(self, conv):
        start_time = time.time()
        last_edit_time = start_time

        while True:
            msg = await conv.get_response()
            current_time = time.time()

            if msg.edit_date and (current_time - msg.edit_date.timestamp()) > 2:
                return msg.text

            if msg.text == "Готово!":
                continue

            await msg.edit(msg.text)
