from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, MessageSegment
from nonebot.log import logger

from .database import database
from .parser import ParserFactory


async def save_group_message_handle(event: GroupMessageEvent, bot: Bot):
    """保存群聊消息"""
    message = event.get_message()
    # 如果消息是回复消息，event.get_message()中不会有reply，需要手动加上
    if reply := event.reply:
        message.insert(0, MessageSegment.reply(reply.message_id))
    content = await ParserFactory.get_content(message, bot)
    if content:
        await database.save_group_message(
            str(event.message_id),
            content,
            str(event.user_id),
            str(event.group_id),
        )
    else:
        logger.warning("没有匹配的解析器，消息将不会记录")
