"""
自习打卡：
@bot 自习帮助
@bot 开始自习
@bot 结束自习
@bot 我的自习数据
@bot 自习修正 3小时30分
"""

from nonebot.rule import to_me
from nonebot.plugin import on_fullmatch, on_command, require

require("nonebot_plugin_guild_patch")

# 注册频道事件，移除本条 import 将导致事件响应器无法接收任何频道消息
from nonebot_plugin_guild_patch import GuildMessageEvent as GuildMessageEvent  # noqa: E402, F401

from .start_clock import clock_in_handle  # noqa: E402
from .end_clock import clock_out_handle  # noqa: E402
from .query_clock import clock_my_statistics_handle  # noqa: E402
from .update_clock import clock_correct_time_handle  # noqa: E402
from .help import clock_help_handle  # noqa: E402
from .utils import is_clock_channel  # noqa: E402


clock_help = on_fullmatch(
    "自习帮助", rule=(to_me() & is_clock_channel), handlers=[clock_help_handle]
)
clock_in = on_fullmatch(
    "开始自习", rule=(to_me() & is_clock_channel), handlers=[clock_in_handle]
)
clock_out = on_fullmatch(
    "结束自习", rule=(to_me() & is_clock_channel), handlers=[clock_out_handle]
)
clock_correct_time = on_command(
    "自习修正", rule=(to_me() & is_clock_channel), handlers=[clock_correct_time_handle]
)
clock_my_statistics = on_fullmatch(
    "我的自习", rule=(to_me() & is_clock_channel), handlers=[clock_my_statistics_handle]
)
