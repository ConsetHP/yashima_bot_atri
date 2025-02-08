from datetime import datetime

from nonebot.matcher import Matcher
from nonebot_plugin_guild_patch import GuildMessageEvent

from .utils import clock_overtime_message
from ..db_model import ClockEventLog, ClockStatus
from ...utils import (
    at_user,
    get_role_id_named,
    set_role,
    get_config,
)
from ...send import send_msgs


async def clock_out_handle(_: Matcher, event: GuildMessageEvent):
    # 检查上一次是否为自动签退
    overtime_model = ClockEventLog.query_overtime(event.get_user_id())
    if overtime_model:
        msg = at_user(event) + clock_overtime_message(overtime_model)
        await send_msgs(event.channel_id, msg)
        return
    # 检查是否正在自习
    working_model = ClockEventLog.query_working(event.get_user_id())
    if not working_model:
        msg = (
            at_user(event)
            + "エラーです、你还没有开始自习呢。请 @bot 自习帮助 来查看帮助"
        )
        await send_msgs(event.channel_id, msg)
        return
    working_model.end_time = datetime.now()
    working_model.status = ClockStatus.FINISH.value
    working_model.update_duration()
    working_model.save()

    msg = at_user(event) + f"已结束自习，本次自习时长{working_model.duration_desc()}"
    await send_msgs(event.channel_id, msg)
    # 修改用户组
    role_id = await get_role_id_named(get_config()["guild"]["clock_role_name"])
    if role_id:
        await set_role(False, role_id, event.get_user_id())
