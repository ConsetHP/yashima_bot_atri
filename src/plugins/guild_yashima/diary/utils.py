import jsonpath_ng as jsonpath

from nonebot import get_bot
from nonebot.log import logger
from nonebot.adapters.qq import Bot
from nonebot.adapters.qq.models.guild import Member, Channel, Role

from ..utils import get_config


def parse_tencent_link_card(json_data: str) -> tuple[str, str] | None:
    """从腾讯的链接卡片提取出标题与链接"""

    def get_json(path: str):
        try:
            return jsonpath.parse(path).find(json_data)[0].value
        except IndexError:
            return None

    app = get_json("$.app")
    link, title = None, None

    if app == "com.tencent.channel.share":
        link = get_json("$.meta.detail.link")
        title = get_json("$.meta.detail.title")
    elif app == "com.tencent.miniapp_01":
        link = get_json("$.meta.detail_1.qqdocurl")
        title = get_json("$.meta.detail_1.desc")
    elif app == "com.tencent.structmsg":
        # 藤子更新了协议，理论上这个已经失效了，但以防万一还是留着
        view = get_json("$.view")
        link = get_json(f"$.meta.{view}.jumpUrl")
        title = get_json(f"$.meta.{view}.title")
    elif app in ["com.tencent.tuwen.lua", "com.tencent.music.lua"]:
        view = get_json("$.view")
        link = get_json(f"$.meta.{view}.jumpUrl")
        title = get_json(f"$.meta.{view}.title")
    else:
        logger.warning(f"无法提取链接：{json_data}")

    return (link, title)


async def get_guild_user(guild_id: str, user_id: str) -> Member:
    """获取频道成员详情"""
    bot: Bot = get_bot(get_config()["general"]["official_bot_id"])
    return await bot.get_member(guild_id=guild_id, user_id=user_id)


async def get_guild_channel(channel_id: str) -> Channel:
    """获取子频道详情"""
    bot: Bot = get_bot(get_config()["general"]["official_bot_id"])
    return await bot.get_channel(channel_id=channel_id)


async def get_guild_roles(guild_id: str) -> list[Role]:
    """获取频道成员身分组列表"""
    bot: Bot = get_bot(get_config()["general"]["official_bot_id"])
    return await bot.get_guild_roles(guild_id=guild_id)
