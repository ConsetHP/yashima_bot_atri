from nonebot.rule import to_me
from nonebot.plugin import on_fullmatch, on_message, require

require("nonebot_plugin_guild_patch")

# 注册频道事件，移除本条 import 将导致事件响应器无法接收任何频道消息
from nonebot_plugin_guild_patch import GuildMessageEvent as GuildMessageEvent  # noqa: E402

from .record import save_guild_img_url_handle, save_recv_guild_msg_handle  # noqa: E402
from .recover import resend_pc_unreadable_msg_handle, resend_system_recalled_img_handle  # noqa: E402


# 记录消息相关
msg_record = on_message(handlers=[save_recv_guild_msg_handle])
img_record = on_message(handlers=[save_guild_img_url_handle])

# 恢复审查系统撤回图片相关
resent_pc_unreadable_msg = on_message(handlers=[resend_pc_unreadable_msg_handle])
recover_last_img = on_fullmatch(
    "我图呢", rule=to_me(), handlers=[resend_system_recalled_img_handle]
)
