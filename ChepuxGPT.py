# meta developer: @chepuxmodules

from .. import loader, utils
import g4f.client
import nest_asyncio
import asyncio

@loader.tds
class ChepuxGPTMod(loader.Module):
    """Задавайте вопросы chatgpt а также генерируйте изображения by @chepuxcat"""
    strings = {"name": "ChepuxGPT"}
    
    generating_image = False
    
    async def client_ready(self, client, db):
        self.client = client

    def __init__(self):
        self.config = loader.ModuleConfig(
            "GPTModel", "gpt-4", "Название модели для генерации ответов"
        )

    async def gptcmd(self, message):
        """Используйте gpt <вопрос> или ответьте на сообщение чтобы спросить вопрос у chatgpt"""
        
        question = utils.get_args_raw(message)
        if not question:
            reply = await message.get_reply_message()
            if reply:
                question = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали вопрос.</b>")
                return

        prompt = [{"role": "user", "content": question}]

        await message.edit("<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую ответ...</b>")
        try:
            client = g4f.client.Client()
            response = client.chat.completions.create(
                model=self.config["GPTMODEL"],
                provider=g4f.Provider.Aichatos,
                messages=prompt
            )
            answer = response.choices[0].message.content
            await utils.answer(message, f"<b><emoji document_id=5409229529392618973>🤔</emoji> Вопрос:</b> {question}\n<b><emoji document_id=5327958075158568158>💃</emoji> Ответ:</b> {answer}")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Произошла ошибка:</b> {e}")

    async def imaginecmd(self, message):
        """Используйте imagine <запрос> или ответьте на сообщение чтобы сгенерировать изображение"""
        
        if self.generating_image:
            await utils.answer(message, "<emoji document_id=5314591660192046611>❌</emoji><b> Сейчас идет генерация другого изображения</b>")
            return
        
        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после imagine</b>")
                return
        
        self.generating_image = True
        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение...</b>")
        await self.client.send_message("@awinic_gpt_bot", "/start")
        await self.client.send_message("@awinic_gpt_bot", "/reset")
        
        await asyncio.sleep(2)
        image_request = f"/image {request_text}"
        await message.client.send_message(7072898560, image_request)

        await asyncio.sleep(20)
        response = await message.client.get_messages(7072898560, limit=1)

        if response and response[0].photo:
            await message.client.send_file(message.to_id, response[0].photo, reply_to=message.id)
            await utils.answer(message, "<b><emoji document_id=5237907553152672597>✅</emoji> Фотография готова, отправил её в ответ на это сообщение!</b>")
        else:
            await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: напишите @chepuxcat</b>")
        self.generating_image = False
        
    async def helpspamcmd(self, message):
        """Используйте gpt <вопрос> или ответьте на сообщение чтобы спросить вопрос у chatgpt"""
        await utils.answer(message, "<b>Если при генерации изображений вам приходят сообщения от другого чата, это нормально.\n\nГенерация изображений происходит через другого бота поетому я вас советую если вас бесят эти уведомления:\n\nЧтобы это исправить поместите в архив @awinic_gpt_bot, а также выключите у него уведомления.</b>")
