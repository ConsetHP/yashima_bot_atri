from typing import Tuple, List, Optional

import tomlkit
from nonebot import Bot, get_bot
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.qq import MessageCreateEvent
from tomlkit.toml_document import TOMLDocument


# region config start
def load_config() -> TOMLDocument:
    with open("config/yashima_config.toml", "r", encoding="utf-8") as file:
        content = file.read()
        logger.info(f"加载yashima_config.toml结果：\n{content}")
        return tomlkit.parse(content)


bot_config = load_config()


def get_config() -> TOMLDocument:
    return bot_config


def reload_config() -> TOMLDocument:
    global bot_config
    bot_config = load_config()
    return bot_config


# region config end


def at_user(event: GuildMessageEvent) -> MessageSegment:
    return MessageSegment.at(event.get_user_id())


def get_sender_id_and_nickname(event: GuildMessageEvent) -> Tuple[str, str]:
    return event.get_user_id(), event.sender.nickname


def get_active_guild_id() -> str:
    return bot_config["guild"]["id"]


def get_bot_id() -> str:
    return bot_config["general"]["bot_id"]


async def get_guild_roles(bot: Bot) -> List[dict]:
    return await bot.get_guild_roles(guild_id=get_active_guild_id())


guild_roles: Optional[List[dict]] = None


async def init_guild_roles():
    global guild_roles
    guild_roles = await get_guild_roles(get_bot(get_bot_id()))
    # logger.info(f"当前身分组列表：{guild_roles}")


async def get_role_id_named(role_name: str) -> Optional[str]:
    if not guild_roles:
        await init_guild_roles()
    for role in guild_roles:
        if role["role_name"] == role_name:
            return role["role_id"]
    logger.warning(f"未匹配到身分组[{role_name}]")
    return None


async def set_role(active: bool, role_id: str, user_id: str):
    await get_bot(get_bot_id()).set_guild_member_role(
        guild_id=get_active_guild_id(), set=active, role_id=role_id, users=[user_id]
    )


async def is_admin_user(event: GuildMessageEvent) -> bool:
    return event.get_user_id() in bot_config["auth"]["admin"]


async def is_me(event: MessageCreateEvent) -> bool:
    """仅用于伪主动matcher的permission"""
    return event.get_user_id() == bot_config["general"]["bot_special_id"]


async def is_normal_channel(event: MessageCreateEvent) -> bool:
    """排除测试频道用的Rule"""
    return event.channel_id != bot_config["debug"]["test_channel_id"]
