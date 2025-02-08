from nonebot_plugin_guild_patch import GuildMessageEvent

from ..db_model import ClockEventLog
from ...utils import get_config


def clock_channel_id() -> str:
    return get_config()["guild"]["clock_channel_id"]


def is_clock_channel(event: GuildMessageEvent) -> bool:
    return clock_channel_id() == str(event.channel_id)


def clock_overtime_message(overtime_model: ClockEventLog) -> str:
    return f"残念ながら、上一次自习({overtime_model.start_time.month}月{overtime_model.start_time.day}日)\n你被自动签退了，请先按命令格式'/自习修正 x小时x分'修正上次的自习数据哦（将x替换成你实际自习的时间）"
