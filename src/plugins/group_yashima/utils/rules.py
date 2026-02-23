from nonebot_plugin_guild_patch import GuildMessageEvent

from ..config import get_config


async def guild_is_admin_user(event: GuildMessageEvent) -> bool:
    return event.get_user_id() == str(get_config().general.bot_admin_tiny_id)
