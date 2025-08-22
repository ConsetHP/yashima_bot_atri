from nonebot.rule import to_me
from nonebot.plugin import on_fullmatch, on_message, require, on_notice

require("nonebot_plugin_guild_patch")

# 注册频道事件，移除本条 import 将导致事件响应器无法接收任何频道消息
from nonebot_plugin_guild_patch import GuildMessageEvent as GuildMessageEvent  # noqa: E402

from . import scheduler as scheduler  # noqa: E402
from .record import save_received_guild_msg_handle  # noqa: E402
from .recover import (  # noqa: E402
    resend_pc_unreadable_msg_handle,
    resend_system_recalled_img_handle,
    notify_system_recalling_handle,
    is_system_operator_recall,
)


# 记录消息相关
msg_record = on_message(handlers=[save_received_guild_msg_handle])

# 恢复审查系统撤回图片相关
resent_pc_unreadable_msg = on_message(handlers=[resend_pc_unreadable_msg_handle])
recover_last_img = on_fullmatch(
    "我图呢", rule=to_me(), handlers=[resend_system_recalled_img_handle]
)

# 标准cqhttp并不会上报系统撤回事件，仅适用于Hyper魔改版的cqhttp
recall_msg_notice = on_notice(
    rule=is_system_operator_recall, handlers=[notify_system_recalling_handle]
)
