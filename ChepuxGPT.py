import requests
import asyncio
import aiohttp
import io
from telethon import functions, types
from .. import loader, utils

@loader.tds
class ChepuxGPTMod(loader.Module):
    """Задавайте вопросы chatgpt а также генерируйте изображения by @chepuxcat"""
    strings = {"name": "ChepuxGPT"}
    
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

        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после imagine</b>")
                return
        
        request_text = request_text.replace(".imagine", "").strip()
        
        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение...</b>")
        
        try:
            image_urls = await self.generate_image(request_text)
            if image_urls:
                await message.client.send_file(message.to_id, image_urls, reply_to=message.id)
                await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> Фотография готова, отправил её в ответ на это сообщение!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {request_text}</b>")
            else:
                await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Не удалось получить изображения.</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Произошла ошибка:</b> {e}")

    async def generate_image(self, prompt):
        """Generate image using the external API"""
        url = 'http://api.onlysq.ru/ai/v2'
        data = {
            "model": "kandinsky",
            "request": {'messages': [{"content": prompt}], "meta": {"image_count": 1}}
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=110) as response:
                response.raise_for_status()
                response_json = await response.json()
                images = response_json.get('answer', [])

                image_files = []
                for image_url in images:
                    async with session.get(image_url) as image_response:
                        image_data = await image_response.read()
                        image_buffer = io.BytesIO(image_data)
                        image_buffer.name = image_url.split('/')[-1]
                        image_files.append(image_buffer)

                return image_files
