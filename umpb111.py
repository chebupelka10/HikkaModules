# meta developer: @chepuxmodules

from .. import loader, utils
import asyncio

@loader.tds
class umpbMod(loader.Module):
    """Поет песни Игоря Желудока by @chepuxbio"""
    strings = {"name": "TT: umpb111"}

    async def kakashkacmd(self, message):
        """Используй .kakashka, чтобы начать петь"""
        lyrics = ["<b><emoji document_id=5388680477408245720>💩</emoji>Сегодня какал сильно тужилсяяя...</b>",
              "<b><emoji document_id=5222474515887435551>🦀</emoji>Из попы кровяная лужицааа...</b>",
              "<b><emoji document_id=5276459351400258810>👎</emoji>И это мне совсем не нравитсяяя...</b>",
              "<b><emoji document_id=5474177367712735995>🥚</emoji>Уже в крови вск мои яицааа.</b>",
              "<b><emoji document_id=5388680477408245720>💩</emoji>Сегодня какал сильно тужилсяяя...</b>",
              "<b><emoji document_id=5222474515887435551>🦀</emoji>Из попы кровяная лужицааа...</b>",
              "<b><emoji document_id=5276459351400258810>👎</emoji>И это мне совсем не нравитсяяя...</b>",
              "<b><emoji document_id=5474177367712735995>🥚</emoji>Уже в крови вск мои яицааа.</b>",]
        for line in lyrics:
            await message.edit(line)
            await asyncio.sleep(2)
