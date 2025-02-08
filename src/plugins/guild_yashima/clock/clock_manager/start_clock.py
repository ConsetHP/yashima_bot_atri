from nonebot.matcher import Matcher
from nonebot_plugin_guild_patch import GuildMessageEvent

from .utils import clock_overtime_message
from ..db_model import ClockEventLog, ClockStatus
from ...utils import (
    get_sender_id_and_nickname,
    at_user,
    get_role_id_named,
    set_role,
    get_config,
)
from ...send import send_msgs


async def clock_in_handle(_: Matcher, event: GuildMessageEvent):
    # 检查上一次是否为自动签退
    overtime_model = ClockEventLog.query_overtime(event.get_user_id())
    if overtime_model:
        msg = at_user(event) + clock_overtime_message(overtime_model)
        await send_msgs(event.channel_id, msg)
        return
    # 检查是否正在自习
    working_model = ClockEventLog.query_working(event.get_user_id())
    if working_model:
        msg = at_user(event) + "你已经打过卡惹"
        await send_msgs(event.channel_id, msg)
        return
    # 入库
    user_id, user_name = get_sender_id_and_nickname(event)
    model = ClockEventLog(
        user_name=user_name, user_id=user_id, status=ClockStatus.WORKING.value
    )
    model.save()
    msg = at_user(event) + "已成功打卡，开始自习"
    await send_msgs(event.channel_id, msg)
    # 修改用户组
    role_id = await get_role_id_named(get_config()["guild"]["clock_role_name"])
    if role_id:
        await set_role(True, role_id, user_id)
