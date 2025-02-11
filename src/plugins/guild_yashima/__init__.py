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
from nonebot.rule import to_me

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
)
from .send import test_sendable_msg_handle  # noqa: E402
from .database.db_init import init_database  # noqa: E402
from .utils import get_config, is_admin_user, reload_config, at_user  # noqa: E402
from .character import Atri  # noqa: E402
from .subscribe.scheduler.manager import init_scheduler  # noqa: E402

# 数据库初始化
init_database(get_config()["db"]["file"])

# 订阅计划任务初始化
get_driver().on_startup(init_scheduler)

reload_config_matcher = on_fullmatch("重载配置", rule=to_me(), permission=is_admin_user)

# 协议适配器的日志里可以看见用户的ID，尽量别用这个指令
my_id_matcher = on_fullmatch(
    "我的ID", ignorecase=True, rule=to_me(), permission=is_admin_user
)

# 萝卜子火箭拳相关
atri_rocket_fists = on_keyword(
    {
        "破铜烂铁",
        "ガラクタ",
        "ポンコツ",
        "がらくた",
        "ぽんこつ",
        "萝卜子",
        "废物",
        "ロボっこ",
        "ロボっコ",
        "ロボっ子",
    },
    rule=(to_me()),
    handlers=[Atri.ping_handle],
)

# 测试 URL 发送相关
test_sendable_msg = on_command(
    "测试发送", handlers=[test_sendable_msg_handle], permission=is_admin_user
)


@reload_config_matcher.handle()
async def _(event: GuildMessageEvent):
    reload_config()
    await reload_config_matcher.send(at_user(event) + "コンフィグがリロードされました")


@my_id_matcher.handle()
async def _(event: GuildMessageEvent):
    await my_id_matcher.send(
        at_user(event) + f"あなたのギルドユーザーIDは：{event.user_id}です"
    )


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
]
