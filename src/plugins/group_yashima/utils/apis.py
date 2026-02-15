"""
对go-cqhttp的api的简单封装，接口详细信息查看https://docs.go-cqhttp.org/api
"""

from nonebot import get_bot

from ..config import get_config


async def get_group_member_info(group_id: str, user_id: str) -> dict:
    """获取群成员信息"""
    bot = get_bot(self_id=get_config().general.bot_qq_id)
    return await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))


async def get_group_info(group_id: str) -> dict:
    """获取群信息"""
    bot = get_bot(self_id=get_config().general.bot_qq_id)
    return await bot.get_group_info(group_id=int(group_id))
