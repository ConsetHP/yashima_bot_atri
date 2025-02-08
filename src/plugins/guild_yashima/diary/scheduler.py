from datetime import timedelta, datetime

from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger

from .db_model import GuildImgRecord, GuildMessageRecord
from ..utils import get_config


@scheduler.scheduled_job("interval", minutes=30, id="clear_overtime_message_record")
async def clear_overtime_message_record():
    msg_save_days = int(get_config()["db"]["msg_save_days"])
    msg_query = GuildMessageRecord.delete().where(
        GuildMessageRecord.recv_time < (datetime.now() - timedelta(days=msg_save_days))
    )
    img_query = GuildImgRecord.delete().where(
        GuildImgRecord.recv_time < (datetime.now() - timedelta(days=msg_save_days))
    )
    msg_num = msg_query.execute()
    img_num = img_query.execute()
    if msg_num > 0 or img_num > 0:
        logger.info(f"已删除频道聊天记录{msg_num}条，聊天图片{img_num}条")
