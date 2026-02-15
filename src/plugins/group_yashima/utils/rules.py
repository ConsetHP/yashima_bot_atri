from nonebot.adapters.onebot.v11 import GroupMessageEvent

from ..config import get_config


async def guild_is_admin_user(event: GroupMessageEvent) -> bool:
    return event.get_user_id() == str(get_config().general.bot_admin_tiny_id)
