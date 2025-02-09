from typing import Union
from datetime import datetime

from nonebot.adapters.minecraft import (
    BaseChatEvent,
    BaseJoinEvent,
    BaseQuitEvent,
    BaseDeathEvent,
)

from .utils import send_mc_msg_to_qq
from ..utils import get_config


CARPET_BOT_PREFIX: list[str] = ["bot_", "BOT_", "Bot_"]  # 地毯模组假人前缀


async def mc_msg_handle(event: Union[BaseChatEvent, BaseDeathEvent]):
    """将 Minecraft 玩家聊天消息发至频道"""
    msg_text = str(event.message)
    timestamp = f"[{datetime.now().strftime('%H:%M:%S')}]"

    # 屏蔽假人死亡消息
    for prefix in CARPET_BOT_PREFIX:
        if msg_text.startswith(prefix) and isinstance(event, BaseDeathEvent):
            return

    msg_result = (
        msg_text
        if isinstance(event, BaseDeathEvent)
        else f"{timestamp} {event.player.nickname} {get_config()['minecraft']['minecraft_message_accent']}{msg_text}"
    )
    await send_mc_msg_to_qq(event.server_name, msg_result)


async def mc_notice_handle(event: Union[BaseJoinEvent, BaseQuitEvent]):
    """将 Minecraft 玩家登录和退出事件发至频道"""

    # 玩家名带假人前缀不发送至频道
    for prefix in CARPET_BOT_PREFIX:
        if event.player.nickname.startswith(prefix):
            return

    msg_result = f"{event.player.nickname} {'加入' if isinstance(event, BaseJoinEvent) else '退出'}了游戏"
    await send_mc_msg_to_qq(event.server_name, msg_result)
