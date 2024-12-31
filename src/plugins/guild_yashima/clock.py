"""
自习打卡：
@bot 自习帮助
@bot 开始自习
@bot 结束自习
@bot 我的自习数据
@bot 自习修正 3小时30分
"""
import re
from datetime import timedelta

from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_apscheduler import scheduler

from .db import *
from .utils import *
from .send import send_msgs


async def clock_help_handle(_: Matcher, event: GuildMessageEvent):
    msg = f"""しばらく中国語モードにスウィッチします、なにせ高性能ですから！
自习打卡相关指令。每次自习最长时间为{get_config()['guild']['clock_overtime']}分钟，超时未结束将自动签退，需修正时间后才能开始新的自习。
@bot 自习帮助
@bot 开始自习
@bot 结束自习
@bot 我的自习   （查询自己的自习统计数据）
@bot /自习修正 3小时30分（或者'2小时'、'45分'等，时长也不能超过上述最长时间，注意开头斜杠）
@bot 破铜烂铁   （抖M福利）"""
    await send_msgs(event.channel_id, msg)


async def clock_my_statistics_handle(_: Matcher, event: GuildMessageEvent):
    user_id = event.get_user_id()
    # 自习次数
    clock_count = (ClockEventLog.select()
                   .where((ClockEventLog.status == ClockStatus.FINISH.value) & (ClockEventLog.user_id == user_id))
                   .count())
    # 自习总时长
    total_duration = (ClockEventLog.select(fn.SUM(ClockEventLog.duration).alias('sum_value'))
                      .where((ClockEventLog.status == ClockStatus.FINISH.value)
                             & (ClockEventLog.user_id == user_id))
                      .scalar())
    msg = at_user(event) + f"你的自习次数：{clock_count}；总时长：{ClockEventLog.to_duration_desc(total_duration)}"
    await send_msgs(event.channel_id, msg)


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
        msg = at_user(event) + f"你已经打过卡惹"
        await send_msgs(event.channel_id, msg)
        return
    # 入库
    user_id, user_name = get_sender_id_and_nickname(event)
    model = ClockEventLog(user_name=user_name, user_id=user_id, status=ClockStatus.WORKING.value)
    model.save()
    msg = at_user(event) + "已成功打卡，开始自习"
    await send_msgs(event.channel_id, msg)
    # 修改用户组。藤子限制了身分组数量，没法加了，暂时注释掉
    # role_id = await get_role_id_named(get_config()['guild']['clock_role_name'])
    # if role_id:
    #     await set_role(True, role_id, user_id)


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
        msg = at_user(event) + f"エラーです、你还没有开始自习呢。请 @bot 自习帮助 来查看帮助"
        await send_msgs(event.channel_id, msg)
        return
    working_model.end_time = datetime.now()
    working_model.status = ClockStatus.FINISH.value
    working_model.update_duration()
    working_model.save()

    msg = at_user(event) + f"已结束自习，本次自习时长{working_model.duration_desc()}"
    await send_msgs(event.channel_id, msg)
    # 修改用户组，注释原因同clock_in_handle
    # role_id = await get_role_id_named(get_config()['guild']['clock_role_name'])
    # if role_id:
    #     await set_role(False, role_id, event.get_user_id())


async def clock_correct_time_handle(_: Matcher, event: GuildMessageEvent, args: Message = CommandArg()):
    model = ClockEventLog.query_overtime(event.get_user_id())
    no_record_err = at_user(event) + f"没有需要修正的记录"
    time_format_err = at_user(event) + f"エラーです、时间格式不正确。正确的格式应为'3小时30分'、'2小时'、'45分'"
    success_msg = f"学習しました、已修正上次自习时长为{model.duration_desc()}"
    if not model:
        await send_msgs(event.channel_id, no_record_err)
        return
    correct_time = args.extract_plain_text().strip()
    match = re.match(r"((?P<hour>\d+)(时|小时))?((?P<minute>\d+)(分|分钟))?", correct_time)
    if not match:
        await send_msgs(event.channel_id, time_format_err)
        return
    hour = int(match.group('hour')) if match.group('hour') else 0
    minute = int(match.group('minute')) if match.group('minute') else 0
    total_minute = 60 * hour + minute
    if total_minute == 0:
        await send_msgs(event.channel_id, time_format_err)
        return

    end_time = model.start_time + timedelta(minutes=total_minute)
    end_time = end_time if end_time < datetime.now() else datetime.now()
    model.end_time = end_time
    model.update_duration()
    model.status = ClockStatus.FINISH.value
    model.save()

    await send_msgs(event.channel_id, success_msg)


@scheduler.scheduled_job('interval', minutes=1, id="clock_find_overtime_and_process")
async def find_overtime_and_process():
    overtime = get_config()['guild']['clock_overtime']
    model_iter = (ClockEventLog.select()
                  .where((ClockEventLog.status == ClockStatus.WORKING.value)
                         & (ClockEventLog.start_time < (datetime.now() - timedelta(minutes=overtime)))))
    for model in model_iter:
        model.end_time = model.start_time + timedelta(minutes=overtime)
        model.status = ClockStatus.OVERTIME.value
        model.update_duration()
        model.save()
        msg = MessageSegment.at(model.user_id) + "自习已超时自动签退，记得修正数据ヾ(￣▽￣)。"
        await send_msgs(clock_channel_id(), msg)
    logger.debug("find_overtime_and_process end")


def clock_channel_id() -> str:
    return get_config()['guild']['clock_channel_id']


def is_clock_channel(event: GuildMessageEvent) -> bool:
    return clock_channel_id() == str(event.channel_id)

def clock_overtime_message(overtime_model: ClockEventLog) -> str:
    return f"残念ながら、上一次自习({overtime_model.start_time.month}月{overtime_model.start_time.day}日)\n你被自动签退了，请先按命令格式'/自习修正 x小时x分'修正上次的自习数据哦（将x替换成你实际自习的时间）"
