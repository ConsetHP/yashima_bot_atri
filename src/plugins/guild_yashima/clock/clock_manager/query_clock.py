from peewee import fn
from nonebot.matcher import Matcher
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..db_model import ClockEventLog, ClockStatus
from ...utils import at_user
from ...send import send_msgs


async def clock_my_statistics_handle(_: Matcher, event: GuildMessageEvent):
    user_id = event.get_user_id()
    # 自习次数
    clock_count = (
        ClockEventLog.select()
        .where(
            (ClockEventLog.status == ClockStatus.FINISH.value)
            & (ClockEventLog.user_id == user_id)
        )
        .count()
    )
    # 自习总时长
    total_duration = (
        ClockEventLog.select(fn.SUM(ClockEventLog.duration).alias("sum_value"))
        .where(
            (ClockEventLog.status == ClockStatus.FINISH.value)
            & (ClockEventLog.user_id == user_id)
        )
        .scalar()
    )
    msg = (
        at_user(event)
        + f"你的自习次数：{clock_count}；总时长：{ClockEventLog.to_duration_desc(total_duration)}"
    )
    await send_msgs(event.channel_id, msg)
