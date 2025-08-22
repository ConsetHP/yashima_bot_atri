from datetime import timedelta, datetime

from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger

from .database.model import GuildMessageRecord
from ..utils import get_config


@scheduler.scheduled_job("interval", minutes=30, id="clear_overtime_message_record")
async def clear_overtime_message_record():
    msg_save_days = int(get_config()["db"]["msg_save_days"])
    msg_query = GuildMessageRecord.delete().where(
        GuildMessageRecord.received_time
        < (datetime.now() - timedelta(days=msg_save_days))
    )
    msg_num = msg_query.execute()
    if msg_num > 0:
        logger.info(f"已删除频道聊天记录{msg_num}条")
