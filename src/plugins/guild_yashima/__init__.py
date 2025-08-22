"""
屋岛作战指挥部专用bot
"""

from nonebot import get_driver
from nonebot.plugin import (
    on_fullmatch,
    on_keyword,
    on_command,
    on_message,
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
from .send import (  # noqa: E402
    test_sendable_msg_handle,
    send_by_official_api_handle,
    send_msgs,
)
from .database.db_init import init_database  # noqa: E402
from .database.base import db  # noqa: E402
from .utils import get_config, is_admin_user, is_me, is_normal_channel, reload_config  # noqa: E402
from .character import atri  # noqa: E402
from .subscribe.scheduler.manager import init_scheduler  # noqa: E402
from .notice import test_disconnect_notice_handle  # noqa: E402

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

# 伪主动相关
send_by_official = on_message(
    rule=is_normal_channel, handlers=[send_by_official_api_handle], permission=is_me
)

# 断连通知
disconnect_notice = on_command(
    "测试掉线通知", handlers=[test_disconnect_notice_handle], permission=is_admin_user
)

# 数据库手动checkpoint
db_checkpoint_matcher = on_fullmatch("更新数据库", permission=is_admin_user)


@db_checkpoint_matcher.handle()
async def checkpint_handler(event: GuildMessageEvent):
    db.execute_sql("PRAGMA wal_checkpoint(FULL);")
    await send_msgs(event.channel_id, "checkpoint successful")


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
