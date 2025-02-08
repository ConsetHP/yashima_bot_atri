import re
from datetime import timedelta, datetime

from nonebot.matcher import Matcher
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters import Message
from nonebot.params import CommandArg

from ..db_model import ClockEventLog, ClockStatus
from ...utils import at_user
from ...send import send_msgs


async def clock_correct_time_handle(
    _: Matcher, event: GuildMessageEvent, args: Message = CommandArg()
):
    model = ClockEventLog.query_overtime(event.get_user_id())
    no_record_err = at_user(event) + "没有需要修正的记录"
    time_format_err = (
        at_user(event)
        + "エラーです、时间格式不正确。正确的格式应为'3小时30分'、'2小时'、'45分'"
    )
    if not model:
        await send_msgs(event.channel_id, no_record_err)
        return
    correct_time = args.extract_plain_text().strip()
    match = re.match(
        r"((?P<hour>\d+)(时|小时))?((?P<minute>\d+)(分|分钟))?", correct_time
    )
    if not match:
        await send_msgs(event.channel_id, time_format_err)
        return
    hour = int(match.group("hour")) if match.group("hour") else 0
    minute = int(match.group("minute")) if match.group("minute") else 0
    total_minute = 60 * hour + minute
    if total_minute == 0:
        await send_msgs(event.channel_id, time_format_err)
        return

    end_time = model.start_time + timedelta(minutes=total_minute)
    end_time = end_time if end_time < datetime.now() else datetime.now()
    model.end_time = end_time
    model.update_duration()
    model.status = ClockStatus.FINISH.value
    model.save()
    success_msg = f"学習しました、已修正上次自习时长为{model.duration_desc()}"

    await send_msgs(event.channel_id, success_msg)
