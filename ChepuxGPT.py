import requests
import asyncio
from telethon import functions, types
from .. import loader, utils

@loader.tds
class ChepuxGPTMod(loader.Module):
    """Задавайте вопросы chatgpt а также генерируйте изображения by @chepuxcat"""
    strings = {"name": "ChepuxGPT"}
    
    generating_image = False
    
    async def client_ready(self, client, db):
        self.client = client

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

        question = question.replace(".gpt", "").strip()
        question = question.replace(".гпт", "").strip()
        
        prompt = [{"role": "user", "content": question}]

        await message.edit("<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую ответ...</b>")
        try:
            response = requests.post('http://api.onlysq.ru/ai/v1', json=prompt)
            response_json = response.json()
            if 'answer' in response_json:
                answer = response_json['answer']
                answer = answer.replace("GPT >>", "").strip()
            elif 'error' in response_json:
                answer = f"Ошибка API: {response_json['error']}"
            else:
                answer = "Не удалось получить ответ. Проверьте API."

            await utils.answer(message, f"<b><emoji document_id=6323343426343404864>❓</emoji> Вопрос:</b> {question}\n<b><emoji document_id=6323463440614557670>☺️</emoji> Ответ:</b> {answer}")
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
        
        request_text = request_text.replace(".imagine", "").strip()
        
        self.generating_image = True
        
        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение...</b>")
        await self.client.send_message("@awinic_gpt_bot", "/start")
        await self.client.send_message("@awinic_gpt_bot", "/reset")
        
        awinic_id = 7072898560
        
        await self.client(functions.account.UpdateNotifySettingsRequest(
            peer=await self.client.get_input_entity(awinic_id),
            settings=types.InputPeerNotifySettings(
            mute_until=2**31 - 1
            )
        ))
        
        await asyncio.sleep(2)
        image_request = f"/image {request_text}"
        await message.client.send_message(awinic_id, image_request)

        await asyncio.sleep(20)
        response = await message.client.get_messages(awinic_id, limit=1)

        if response and response[0].photo:
            await message.client.send_file(message.to_id, response[0].photo, reply_to=message.id)
            await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> Фотография готова, отправил её в ответ на это сообщение!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {request_text}</b>")
        else:
            await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Вы используете ненормативную лексику в запросе который была заблокирован, либо вы ввели пустой запрос.</b>")
        
        self.generating_image = False
