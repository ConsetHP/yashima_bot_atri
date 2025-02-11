from nonebot.rule import to_me  # noqa: E402
from nonebot.plugin import on_command, require  # noqa: E402

require("nonebot_plugin_guild_patch")

# 注册频道事件，移除本条 import 将导致事件响应器无法接收任何频道消息
from nonebot_plugin_guild_patch import GuildMessageEvent as GuildMessageEvent  # noqa: E402

from .chart_manager import compare_seniority_on_channels  # noqa: E402
from ..utils import is_admin_user  # noqa: E402


compare_seniority_matcher = on_command(
    "对比老登含量", rule=to_me(), permission=is_admin_user, block=True
)
compare_seniority_on_channels(compare_seniority_matcher)
