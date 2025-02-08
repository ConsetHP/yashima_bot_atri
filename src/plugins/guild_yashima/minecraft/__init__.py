"""
QQ 频道消息和 Minecraft 服务器消息互通
参考 https://github.com/17TheWord/nonebot-plugin-mcqq
"""

from nonebot.plugin import on_message, on_notice, require

require("nonebot_plugin_guild_patch")

# 注册频道事件，移除本条 import 将导致事件响应器无法接收任何频道消息
from nonebot_plugin_guild_patch import GuildMessageEvent as GuildMessageEvent  # noqa: E402, F401

from .server_msg import mc_msg_handle, mc_notice_handle  # noqa: E402
from .qq_msg import qq_msg_handle  # noqa: E402
from .utils import mc_msg_rule, is_minecraft_channel  # noqa: E402


mc_to_qq_msg = on_message(rule=mc_msg_rule, handlers=[mc_msg_handle])
mc_to_qq_notice = on_notice(rule=mc_msg_rule, handlers=[mc_notice_handle])
qq_to_mc_msg = on_message(rule=is_minecraft_channel, handlers=[qq_msg_handle])
