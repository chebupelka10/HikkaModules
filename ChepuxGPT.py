import requests
import asyncio
from telethon import functions, types
from .. import loader, utils
import aiohttp
import io

@loader.tds
class ChepuxGPTMod(loader.Module):
    """Задавайте вопросы chatgpt, а также генерируйте изображения by @chepuxcat"""
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
        """Используйте imagine <запрос> чтобы сгенерировать изображение. Можно указать количество изображений через <кол-во>"""
        
        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после imagine</b>")
                return
        
        request_text = request_text.replace(".imagine", "").strip()

        # Разделяем запрос на описание и количество изображений
        parts = request_text.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            image_count = int(parts[1])
            prompt = parts[0]
        else:
            image_count = 1
            prompt = request_text

        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение...</b>")

        try:
            dict_to_send = {
                "model": "kandinsky",
                "request": {'messages': [{"content": prompt}], "meta": {"image_count": image_count}}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post('http://api.onlysq.ru/ai/v2', json=dict_to_send, timeout=110) as response:
                    response.raise_for_status()
                    response_json = await response.json()

                    images = response_json.get('answer', [])
                    
                    for index, image_url in enumerate(images):
                        image_url = image_url.replace('https://', 'http://')
                        async with session.get(image_url) as image_response:
                            image_data = await image_response.read()
                            image_buffer = io.BytesIO(image_data)
                            image_buffer.name = image_url.split('/')[-1]
                            await message.client.send_file(message.to_id, image_buffer, reply_to=message.id)

                    if images:
                        await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> Изображение(-я) готово(-ы)!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {prompt}</b>")
                    else:
                        await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Не удалось получить изображения от API.</b>")
        except aiohttp.ClientError as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка при запросе к API:</b> {e}")
        except ValueError:
            await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка при обработке ответа от API.</b>")
