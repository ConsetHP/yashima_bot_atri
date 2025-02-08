from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.log import logger
from nonebot import Bot

from .utils import parse_qq_msg_to_base_model, send_qq_msg_to_mc
from ..utils import get_config


async def qq_msg_handle(bot: Bot, event: GuildMessageEvent):
    """将 QQ 频道聊天消息发至 Minecraft"""
    if server_name := get_config()["minecraft"]["server_name"]:
        message, log_text = await parse_qq_msg_to_base_model(bot=bot, event=event)
        result_log_text = (
            f"返回结果：\n发送至服务器 {server_name} 的命令结果：\n{log_text}"
        )
        logger.info(result_log_text)
        await send_qq_msg_to_mc(server_name, message)
