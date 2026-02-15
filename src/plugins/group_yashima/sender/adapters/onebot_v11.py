from nonebot.adapters import Bot, Message
from nonebot.adapters.onebot.v11 import Bot as OB11Bot, Message as OB11Message

from ..bot import BotSelecter
from ..model import AdapterName, SendTarget, TargetQQGroup, TargetQQGuildOB11


@BotSelecter.register_sender(AdapterName.one_bot_v11)
async def _send_ob11msg(bot: Bot, target: SendTarget, msg: Message):
    assert isinstance(bot, OB11Bot)
    assert isinstance(msg, OB11Message)

    if isinstance(target, TargetQQGroup):
        await bot.send_group_msg(group_id=target.group_id, message=msg)
    elif isinstance(target, TargetQQGuildOB11):
        await bot.send_guild_channel_msg(
            guild_id=target.guild_id, channel_id=target.channel_id, message=msg
        )
    else:
        raise RuntimeError(f"target {target.__class__.__name__} not supported")
