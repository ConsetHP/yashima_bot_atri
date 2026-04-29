from datetime import datetime, timedelta

from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends

from .daily_report import get_daily_report
from ..sender import send_msgs, TargetQQGuildOB11
from ..config import get_config


async def check_param(
    matcher: Matcher, event: GuildMessageEvent, args: Message = CommandArg()
):
    if args and args.extract_plain_text() not in ["今天", "今日", "昨天", "昨日"]:
        await matcher.finish(
            Message.template(
                "未知参数：{}，支持的参数：\n今天\n昨天\n示例：\n每日报告 昨天"
            ).format(args.extract_plain_text()),
        )
    return event


def get_day_start(args: Message = CommandArg()) -> datetime:
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    yesterday_start = today_start - timedelta(days=1)
    if not args or args.extract_plain_text() in ["今天", "今日"]:
        day_start = today_start
    else:
        day_start = yesterday_start
    return day_start


async def send_report(
    _: Matcher,
    event: GuildMessageEvent = Depends(check_param),
    day_start=Depends(get_day_start, use_cache=False),
):
    target = TargetQQGuildOB11(
        bot_id=get_config().general.bot_qq_id,
        guild_id=get_config().sender.target_guild,
        channel_id=str(event.channel_id),
    )
    report = await get_daily_report(str(get_config().analyzer.target_group), day_start)
    await send_msgs(
        target,
        msg=Message(MessageSegment.image(report)),
    )
