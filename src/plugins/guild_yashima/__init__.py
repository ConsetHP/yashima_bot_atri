"""
屋岛作战指挥部专用bot
"""

from nonebot import get_driver
from nonebot.plugin import (
    on_fullmatch,
    on_keyword,
    on_command,
    require,
)

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_guild_patch")

from nonebot_plugin_guild_patch import GuildMessageEvent  # noqa: E402

from . import (  # noqa: E402
    diary,
    minecraft,
    subscribe,
    wrdcld,
    clock,
    send,
    guild_plan,
    forum,
)
from .send import test_sendable_msg_handle, send_msgs  # noqa: E402
from .database.db_init import init_database  # noqa: E402
from .utils import get_config, is_admin_user, reload_config  # noqa: E402
from .character import atri  # noqa: E402
from .subscribe.scheduler.manager import init_scheduler  # noqa: E402

# 数据库初始化
init_database(get_config()["db"]["file"])

# 订阅计划任务初始化
get_driver().on_startup(init_scheduler)

reload_config_matcher = on_fullmatch("重载配置", permission=is_admin_user)


# 萝卜子火箭拳相关
atri_rocket_fists = on_keyword(
    {"ポンコツ"},
    handlers=[atri.qq_ping_handle, atri.cqhttp_ping_handle],
)

# 测试 URL 发送相关
test_sendable_msg = on_command(
    "测试发送", handlers=[test_sendable_msg_handle], permission=is_admin_user
)


@reload_config_matcher.handle()
async def _(event: GuildMessageEvent):
    reload_config()
    await send_msgs(event.channel_id, "ok")


__all__ = [
    "wrdcld",
    "diary",
    "subscribe",
    "minecraft",
    "database",
    "clock",
    "guild_plan",
    "send",
    "utils",
    "forum",
]
