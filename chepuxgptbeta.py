import time
from telethon import types, events
from .. import loader, utils

@loader.tds
class ChepuxGPTBetaMod(loader.Module):
    """Позволяет разговаривать с ChatGPT без api key"""
    is_generating = False  # Флаг состояния для проверки, идет ли генерация ответа

    strings = {
        "name": "ChepuxGPT",
        "generating": "Генерирую ответ...",
        "question": "Вопрос: {}",
        "answer": "Ответ: {}",
        "busy": "Подождите, пока будет сгенерирован предыдущий ответ."
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.command()
    async def gptcmd(self, message: types.Message):
        """Новая тема + задать вопрос"""
        if self.is_generating:
            await utils.answer(message, self.strings["busy"])
            return

        query = utils.get_args_raw(message)
        if not query:
            await utils.answer(message, "Укажите запрос после команды .gptcmd")
            return

        self.is_generating = True  # Устанавливаем флаг в True, начинается генерация ответа
        bot_id = 7072898560
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
        self.is_generating = False  # Сбрасываем флаг после получения ответа

    async def _get_response(self, conv):
        start_time = time.time()
        last_edit_time = start_time
        last_msg = None

        while True:
            msg = await conv.get_response()
            current_time = time.time()

            if msg == last_msg and (current_time - last_edit_time) > 2:
                return msg.text

            if msg.text != last_msg:
                last_edit_time = current_time
                last_msg = msg.text

            if msg.text == "Готово!":
                continue
