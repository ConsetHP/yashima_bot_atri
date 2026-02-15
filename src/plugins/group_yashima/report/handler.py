from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.matcher import Matcher

from .daily_report import get_daily_report
from ..sender import send_msgs, TargetQQGuildOB11
from ..config import get_config


async def send_report(_: Matcher, event: GuildMessageEvent):
    report = await get_daily_report()
    await send_msgs(
        TargetQQGuildOB11(
            bot_id=get_config().general.bot_qq_id,
            guild_id=get_config().sender.target_guild,
            channel_id=str(event.channel_id),
        ),
        msg=Message(MessageSegment.image(report)),
    )
