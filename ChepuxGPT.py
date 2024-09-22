import requests
import asyncio
from telethon import functions, types
from .. import loader, utils
import aiohttp
import io

@loader.tds
class OnlySqAPIMod(loader.Module):
    """Задавайте вопросы с помощью разных моделей GPT, а также генерируйте изображения by @chepuxcat, основанный на OnlySq api."""
    strings = {"name": "OnlySqAPI"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            "IS_18_PLUS", False, lambda m: self.strings["name"],
            "GPT_MODEL", "ChatGPT", lambda m: self.strings["name"],  # Добавлен выбор модели GPT
            "IMG_MODEL", "Kandinsky", lambda m: self.strings["name"],  # Добавлен выбор модели для изображений
        )
        self.gpt_models = ["ChatGPT", "Gemini", "Blackbox"]
        self.image_models = ["Kandinsky", "Flux"]

    async def client_ready(self, client, db):
        self.client = client

    def _get_model_prompt(self, model, question):
        if model == "ChatGPT":
            return [{"role": "user", "content": question}]
        elif model == "gemini":
            return {"model": "gemini", "request": {"messages": [{"content": question}], "meta": {}}}
        elif model == "blackbox":
            return {"model": "blackbox", "request": {"messages": [{"role": "user", "content": question}]}}
        else:
            return None

    def _get_image_model_prompt(self, model, prompt, image_count=1):
        if model == "Kandinsky":
            return {
                "model": "kandinsky",
                "request": {
                    "messages": [{"role": "user", "content": prompt}],
                    "meta": {"image_count": image_count}
                }
            }
        elif model == "Flux":
            return {
                "model": "flux",
                "request": {
                    "messages": [{"content": prompt}]
                }
            }
        else:
            return None

    async def aicmd(self, message):
        """Используйте ai <вопрос> или ответьте на сообщение, чтобы спросить вопрос у выбранной модели"""
        question = utils.get_args_raw(message)
        if not question:
            reply = await message.get_reply_message()
            if reply:
                question = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали вопрос.</b>")
                return

        question = question.replace(".ai", "").strip()
        
        selected_model = self.config["GPT_MODEL"]
        prompt = self._get_model_prompt(selected_model, question)

        if not prompt:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Модель \"{selected_model}\" не поддерживается. Выберите одну из доступных моделей: ChatGPT, gemini, blackbox. Выбрать их можно в конфиге, в разделе GPT_MODEL</b>")
            return

        await message.edit(f"<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую ответ с помощью {selected_model}...</b>")
        try:
            api_url = 'https://api.onlysq.ru/ai/v1' if selected_model == "ChatGPT" else 'https://api.onlysq.ru/ai/v2'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=prompt) as response:
                    response.raise_for_status()
                    response_json = await response.json()
                    if 'answer' in response_json:
                        answer = response_json['answer'].replace("GPT >>", "").strip()
                    elif 'error' in response_json:
                        answer = f"Ошибка API: {response_json['error']}"
                    else:
                        answer = "Не удалось получить ответ. Проверьте API."
            
            await utils.answer(message, f"<b><emoji document_id=6323343426343404864>❓</emoji> Вопрос:</b> {question}\n<b><emoji document_id=6323463440614557670>☺️</emoji> Ответ:</b> {answer}\n\n<b>Сгенерированно с помощью {selected_model}</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Произошла ошибка:</b> {e}")

    async def imgaicmd(self, message):
        """Используйте imgai <запрос> чтобы сгенерировать изображение."""
        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после imgai</b>")
                return
        
        request_text = request_text.replace(".imgai", "").strip()

        parts = request_text.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            image_count = int(parts[1])
            prompt = parts[0]
        else:
            image_count = 1
            prompt = request_text

        selected_image_model = self.config["IMG_MODEL"]
        image_prompt = self._get_image_model_prompt(selected_image_model, prompt, image_count)

        if not image_prompt:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Модель \"{selected_image_model}\" не поддерживается. Выберите одну из доступных моделей: Kandinsky, Flux.</b>")
            return

        await utils.answer(message, f"<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение с помощью {selected_image_model}...</b>")

        try:
            api_url = 'https://api.onlysq.ru/ai/v2'

            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=image_prompt, timeout=110) as response:
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
                        await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> Изображение(-я) готово(-ы)! Оно было отправлено в ответ на это сообщение!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {prompt}\n\nСгенерированно с помощью {selected_image_model}</b>")
                    else:
                        await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Не удалось получить изображения от API.</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка при запросе к API:</b> {e}")
            
    async def imaginensfwcmd(self, message):
        """Используйте imaginensfw <запрос> чтобы сгенерировать изображение. Только 18+, вам надо подтвердить что вам 18+"""

        if not self.config["IS_18_PLUS"]:
            await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Генерация NSFW контента недоступна. Вы должны подтвердить, что вам 18+ в конфиге. Поставив в IS_18_PLUS значение: True, или написав <code>fcfg OnlySqAPI IS_18_PLUS True</code></b>")
            return
        
        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после imaginensfw</b>")
                return
        
        request_text = request_text.replace(".imaginensfw", "").strip()

        parts = request_text.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            image_count = int(parts[1])
            prompt = parts[0]
        else:
            image_count = 1
            prompt = request_text

        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую NSFW изображение...</b>")

        try:
            dict_to_send = {
                "model": "nsfw-xl",
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
                        await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> NSFW изображение готово! Оно было отправленно в ответ на это сообщение!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {prompt}</b>")
                    else:
                        await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Не удалось получить изображения от API.</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка при запросе к API:</b> {e}")
            
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

        await message.edit("<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую ответ с помощью ChatGPT...</b>")
        try:
            response = requests.post('https://api.onlysq.ru/ai/v1', json=prompt)
            response_json = response.json()
            if 'answer' in response_json:
                answer = response_json['answer']
                answer = answer.replace("GPT >>", "").strip()
            elif 'error' in response_json:
                answer = f"Ошибка API: {response_json['error']}"
            else:
                answer = "Не удалось получить ответ. Проверьте API."

            await utils.answer(message, f"<b><emoji document_id=6323343426343404864>❓</emoji> Вопрос:</b> {question}\n<b><emoji document_id=6323463440614557670>☺️</emoji> Ответ:</b> {answer}\n\n<b>Сгенерированно с помощью ChatGPT</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Произошла ошибка:</b> {e}")
            
    async def geminicmd(self, message):
        """Используйте gemini <вопрос> или ответьте на сообщение, чтобы спросить вопрос у Gemini"""
        
        question = utils.get_args_raw(message)
        if not question:
            reply = await message.get_reply_message()
            if reply:
                question = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали вопрос.</b>")
                return

        question = question.replace(".gemini", "").strip()
        
        dictToSend = {"model": "gemini", "request": {"messages": [{"content": question}]}}

        await message.edit("<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую ответ с помощью Gemini...</b>")
        try:
            response = requests.post('https://api.onlysq.ru/ai/v2', json=dictToSend)
            response_json = response.json()
            if 'answer' in response_json:
                answer = response_json['answer']
            elif 'error' in response_json:
                answer = f"Ошибка API: {response_json['error']}"
            else:
                answer = "Не удалось получить ответ. Проверьте API."

            await utils.answer(message, f"<b><emoji document_id=6323343426343404864>❓</emoji> Вопрос:</b> {question}\n<b><emoji document_id=6323463440614557670>☺️</emoji> Ответ:</b> {answer}\n\n<b>Сгенерировано с помощью Gemini</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Произошла ошибка:</b> {e}")
            
    async def bbcmd(self, message):
        """Используйте bb <вопрос> или ответьте на сообщение, чтобы спросить вопрос у Blackbox"""
        
        question = utils.get_args_raw(message)
        if not question:
            reply = await message.get_reply_message()
            if reply:
                question = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали вопрос.</b>")
                return

        question = question.replace(".bb", "").strip()
        
        dictToSend = {"model": "blackbox", "request": {"messages": [{"content": question}]}}

        await message.edit("<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую ответ с помощью Blackbox...</b>")
        try:
            response = requests.post('https://api.onlysq.ru/ai/v2', json=dictToSend)
            response_json = response.json()
            if 'answer' in response_json:
                answer = response_json['answer']
            elif 'error' in response_json:
                answer = f"Ошибка API: {response_json['error']}"
            else:
                answer = "Не удалось получить ответ. Проверьте API."

            await utils.answer(message, f"<b><emoji document_id=6323343426343404864>❓</emoji> Вопрос:</b> {question}\n<b><emoji document_id=6323463440614557670>☺️</emoji> Ответ:</b> {answer}\n\n<b>Сгенерировано с помощью Blackbox</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Произошла ошибка:</b> {e}")
            
    async def fluxcmd(self, message):
        """Используйте flux <запрос> чтобы сгенерировать изображение."""
        
        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после flux</b>")
                return
        
        request_text = request_text.replace(".flux", "").strip()

        parts = request_text.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            image_count = int(parts[1])
            prompt = parts[0]
        else:
            image_count = 1
            prompt = request_text

        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение с помощью flux...</b>")

        try:
            dict_to_send = {
                "model": "flux",
                "request": {'messages': [{"content": prompt}], "meta": {"image_count": image_count}}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.onlysq.ru/ai/v2', json=dict_to_send, timeout=110) as response:
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
                        await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> Изображение готово! Оно было отправленно в ответ на это сообщение!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {prompt}\nСгенерированно с помощью flux</b>")
                    else:
                        await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Не удалось получить изображения от API.</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка при запросе к API:</b> {e}")
            
    async def kandinskycmd(self, message):
        """Используйте kandinsky <запрос> чтобы сгенерировать изображение."""
        
        request_text = utils.get_args_raw(message)
        if not request_text:
            reply = await message.get_reply_message()
            if reply:
                request_text = reply.raw_text
            else:
                await utils.answer(message, "<b><emoji document_id=5321288244350951776>👎</emoji> Вы не задали описание изображения после kandinsky</b>")
                return
        
        request_text = request_text.replace(".kandinsky", "").strip()

        parts = request_text.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            image_count = int(parts[1])
            prompt = parts[0]
        else:
            image_count = 1
            prompt = request_text

        await utils.answer(message, "<b><emoji document_id=5409143295039252230>🔄</emoji> Генерирую изображение с помощью kandinsky...</b>")

        try:
            dict_to_send = {
                "model": "kandinsky",
                "request": {'messages': [{"content": prompt}], "meta": {"image_count": image_count}}
            }

            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.onlysq.ru/ai/v2', json=dict_to_send, timeout=110) as response:
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
                        await utils.answer(message, f"<b><emoji document_id=5237907553152672597>✅</emoji> Изображение готово! Оно было отправленно в ответ на это сообщение!\n\n<emoji document_id=6323343426343404864>❓</emoji> Запрос для генерации: {prompt}\nСгенерированно с помощью kandinsky</b>")
                    else:
                        await utils.answer(message, "<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка: Не удалось получить изображения от API.</b>")
        except Exception as e:
            await utils.answer(message, f"<b><emoji document_id=5314591660192046611>❌</emoji> Ошибка при запросе к API:</b> {e}")
