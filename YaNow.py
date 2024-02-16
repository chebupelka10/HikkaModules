from hikka.modules import loader
from hikka.utils import utils

@loader.tds
class YaNowMod(loader.Module):
    """Interact with YaNowBot"""
    strings = {"name": "YaNow"}

    async def ynowcmd(self, message):
        """Send inline query to YaNowBot and click the first result"""
        await utils.answer(message, "Sending inline query to YaNowBot...")
        results = await message.client.inline_query("@YaNowBot", "")
        if results:
            await results[0].click(message.to_id, hide_via=True)
            await message.delete()
        else:
            await utils.answer(message, "No results from YaNowBot")

    async def ysettokencmd(self, message):
        """Send /token command to YaNowBot with arguments"""
        args = utils.get_args(message)
        if args:
            await utils.answer(message, "Sending /token command to YaNowBot...")
            await message.client.send_message("@YaNowBot", "/token " + " ".join(args))
            await message.delete()
        else:
            await utils.answer(message, "Please provide some arguments for /token command")
