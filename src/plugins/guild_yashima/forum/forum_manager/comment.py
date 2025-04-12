"""
帖子评论提醒，待实现
"""

from typing import Union

from nonebot.log import logger
from nonebot.adapters.qq import (
    Bot,
    ForumPostCreateEvent,
    ForumReplyCreateEvent,
    ActionFailed,
)


async def receive_comment(
    bot: Bot, event: Union[ForumPostCreateEvent, ForumReplyCreateEvent]
):
    """帖子评论提醒待实现"""
    logger.info(f"收到帖子EVENT：{type(event)}")
    logger.info(f"用户id：{event.author_id}")
    nick_name = "未知昵称"
    try:
        nick_name = (
            await bot.get_member(guild_id=event.guild_id, user_id=event.author_id)
        ).nick
    except ActionFailed as af:
        logger.warning(f"无法获取昵称：{af}，用户id：{event.author_id}")
    logger.info(f"用户昵称：{nick_name}")
