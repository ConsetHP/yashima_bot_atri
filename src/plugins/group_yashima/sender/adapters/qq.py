from nonebot.adapters import Bot, Message
from nonebot.adapters.qq import Bot as QQBot, Message as QQMessage

from ..bot import BotSelecter
from ..model import AdapterName, TargetQQGuildOfficial, SendTarget


@BotSelecter.register_sender(AdapterName.qq)
async def _send_qqmsg(bot: Bot, target: SendTarget, msg: Message):
    assert isinstance(bot, QQBot)
    assert isinstance(msg, QQMessage)

    if isinstance(target, TargetQQGuildOfficial):
        await bot.send_to_channel(channel_id=target.channel_id, message=msg)
    else:
        raise RuntimeError(f"target {target.__class__.__name__} not supported")
