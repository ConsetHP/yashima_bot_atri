from io import BytesIO

from nonebot import get_bot
from nonebot.exception import ActionFailed
from datetime import datetime
from matplotlib.figure import Figure

from ..utils import get_active_guild_id, get_bot_id


async def get_chat_channels():
    """获取聊天子频道列表"""
    raw_channels = await get_bot(get_bot_id()).get_guild_channel_list(
        guild_id=get_active_guild_id(), no_cache=True
    )
    return [
        per_channel for per_channel in raw_channels if per_channel["channel_type"] == 1
    ]


async def get_channel_name(channel_id: int | str) -> str:
    """获取子频道名称"""
    raw_channels = await get_bot(get_bot_id()).get_guild_channel_list(
        guild_id=get_active_guild_id(), no_cache=True
    )
    for per_channel in raw_channels:
        if str(channel_id) == per_channel["channel_id"]:
            return per_channel["channel_name"]


def remove_duplicates(lst):
    return list(dict.fromkeys(lst))


def save_figure_to_bytes(figure: Figure):
    image_bytes = BytesIO()
    figure.savefig(image_bytes, format="png")
    image_bytes.seek(0)
    return image_bytes.getvalue()


async def get_days_since_joined(user_id: int | str) -> int:
    """获取用户的入频时间"""
    try:
        raw_time = (
            await get_bot(get_bot_id()).get_guild_member_profile(
                guild_id=get_active_guild_id(), user_id=str(user_id)
            )
        )["join_time"]
    except ActionFailed as _:
        # 退频用户会导致这个Exception，当作0天算吧
        return 0
    joined_date = datetime.fromtimestamp(raw_time)
    delta = datetime.now() - joined_date
    return delta.days
