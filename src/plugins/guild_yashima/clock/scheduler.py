from datetime import timedelta, datetime

from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger

from .db_model import ClockEventLog, ClockStatus
from .clock_manager.utils import clock_channel_id
from ..utils import get_config
from ..send import send_msgs


@scheduler.scheduled_job("interval", minutes=1, id="clock_find_overtime_and_process")
async def find_overtime_and_process():
    overtime = get_config()["guild"]["clock_overtime"]
    model_iter = ClockEventLog.select().where(
        (ClockEventLog.status == ClockStatus.WORKING.value)
        & (ClockEventLog.start_time < (datetime.now() - timedelta(minutes=overtime)))
    )
    for model in model_iter:
        model.end_time = model.start_time + timedelta(minutes=overtime)
        model.status = ClockStatus.OVERTIME.value
        model.update_duration()
        model.save()
        msg = (
            MessageSegment.at(model.user_id)
            + "自习已超时自动签退，记得修正数据ヾ(￣▽￣)。（如果不知道如何修正，请查看子频道精华消息或 @bot 自习帮助）"
        )
        await send_msgs(clock_channel_id(), msg)
    logger.debug("find_overtime_and_process end")
