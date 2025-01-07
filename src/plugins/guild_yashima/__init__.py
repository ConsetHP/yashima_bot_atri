"""
屋岛作战指挥部专用bot
"""

from nonebot import get_driver
from nonebot.plugin import (
    on_fullmatch,
    on_message,
    on_keyword,
    on_command,
    require,
    on_notice,
)
from nonebot.rule import to_me

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_guild_patch")

from nonebot_plugin_guild_patch import GuildMessageEvent  # noqa: E402

from . import (  # noqa: E402
    db,
    clock,
    records,
    minecraft_msg,
    character,
    db_config,
    platform,
    post,
    scheduler,
    send,
    sub_manager,
    theme,
    types,
    utils,
)
from .clock import (  # noqa: E402
    is_clock_channel,
    clock_help_handle,
    clock_in_handle,
    clock_out_handle,
    clock_correct_time_handle,
    clock_my_statistics_handle,
)
from .records import (  # noqa: E402
    save_recv_guild_msg_handle,
    save_guild_img_url_handle,
    resend_pc_unreadable_msg_handle,
    yesterday_wordcloud_handle,
    resend_system_recalled_img_handle,
)
from .db import init_database  # noqa: E402
from .utils.utils import get_config, is_admin_user, reload_config, at_user  # noqa: E402
from .character import Atri  # noqa: E402
from .minecraft_msg import (  # noqa: E402
    mc_msg_handle,
    mc_msg_rule,
    mc_notice_handle,
    is_minecraft_channel,
    qq_msg_handle,
)
from .scheduler.manager import init_scheduler  # noqa: E402

# 数据库初始化
init_database(get_config()["db"]["file"])

# 计划任务初始化
get_driver().on_startup(init_scheduler)


reload_config_matcher = on_fullmatch("重载配置", rule=to_me(), permission=is_admin_user)
my_id_matcher = on_fullmatch("我的ID", ignorecase=True, rule=to_me())

# 打卡相关
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

# 萝卜子火箭拳相关
clock_rocket_fists = on_keyword(
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

# 词云相关
msg_record = on_message(handlers=[save_recv_guild_msg_handle])
resent_pc_unreadable_msg = on_message(handlers=[resend_pc_unreadable_msg_handle])
yesterday_wordcloud = on_command(
    "昨日词云",
    rule=to_me(),
    permission=is_admin_user,
    handlers=[yesterday_wordcloud_handle],
)

# 恢复审查系统撤回图片相关
img_record = on_message(handlers=[save_guild_img_url_handle])
recover_last_img = on_fullmatch(
    "我图呢", rule=to_me(), handlers=[resend_system_recalled_img_handle]
)

# QQ MC 消息转发相关
mc_to_qq_msg = on_message(rule=mc_msg_rule, handlers=[mc_msg_handle])
mc_to_qq_notice = on_notice(rule=mc_msg_rule, handlers=[mc_notice_handle])
qq_to_mc_msg = on_message(rule=is_minecraft_channel, handlers=[qq_msg_handle])


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
    "db",
    "clock",
    "records",
    "minecraft_msg",
    "character",
    "db_config",
    "platform",
    "post",
    "scheduler",
    "send",
    "sub_manager",
    "theme",
    "types",
    "utils",
]
