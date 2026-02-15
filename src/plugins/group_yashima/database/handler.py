from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .model import db


async def checkpoint_handler(matcher: Matcher, event: GroupMessageEvent):
    """手动将数据库缓存存入硬盘，调试用"""
    try:
        db.execute_sql("PRAGMA wal_checkpoint(FULL);")
    except Exception as ex:
        await matcher.finish(f"checkpoint failed: {ex}")
    else:
        await matcher.finish("checkpoint successful")
