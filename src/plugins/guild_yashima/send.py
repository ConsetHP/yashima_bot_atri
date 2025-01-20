"""
消息发送队列
参考 https://github.com/MountainDash/nonebot-bison
"""

import asyncio
from collections import deque
from typing import Union

from nonebot import get_bot
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters import Message
from nonebot.log import logger

from .utils.utils import get_config, get_active_guild_id

QUEUE: deque[tuple[str, Message | str, int]] = deque()

MESSAGE_SEND_INTERVAL = get_config()["general"]["send_interval"]
MESSAGE_SEND_RETRY = get_config()["general"]["send_failure_retry"]

_MESSAGE_DISPATCH_TASKS: set[asyncio.Task] = set()


async def _do_send(channel_id: str, msg: Message | str):
    try:
        await get_bot(get_config()["general"]["bot_id"]).send_guild_channel_msg(
            guild_id=get_active_guild_id(), channel_id=channel_id, message=msg
        )
    except ActionFailed:
        logger.warning("发送消息失败")


async def do_send_msgs():
    """处理队列中的消息发送任务"""
    if not QUEUE:
        return
    while True:
        # 先读取队列再pop任务，如果先pop，队列长度变成0，此时加入新任务会导致函数被重复执行
        channel_id, msg, retry_time = QUEUE[0]
        try:
            await _do_send(channel_id, msg)
        except Exception as e:
            await asyncio.sleep(MESSAGE_SEND_INTERVAL)
            QUEUE.popleft()
            if retry_time > 0:
                logger.warning(f"消息发送失败, 剩余重试次数: {retry_time}")
                QUEUE.appendleft((channel_id, msg, retry_time - 1))
            else:
                msg_str = str(msg)
                if len(msg_str) > 50:
                    msg_str = msg_str[:50] + "..."
                logger.warning(f"重试次数耗尽，发送消息错误： {e} {msg_str}")
        else:
            # 先sleep后pop，否则会出现上条注释提到的重复执行错误
            await asyncio.sleep(MESSAGE_SEND_INTERVAL)
            QUEUE.popleft()
        finally:
            if not QUEUE:
                return


async def _send_msgs_dispatch(channel_id: str, msg: Message | str):
    QUEUE.append((channel_id, msg, MESSAGE_SEND_RETRY))
    # 队列长度在 append 前是 0
    if len(QUEUE) == 1:
        task = asyncio.create_task(do_send_msgs())
        _MESSAGE_DISPATCH_TASKS.add(task)
        task.add_done_callback(_MESSAGE_DISPATCH_TASKS.discard)


async def send_msgs(channel_id: str | int, msg: Union[Message, str, list[Message]]):
    """将消息发送任务添加至队列"""
    if type(channel_id) is int:
        channel_id = str(channel_id)
    if type(msg) is list:
        for per_msg in msg:
            await _send_msgs_dispatch(channel_id, per_msg)
    else:
        await _send_msgs_dispatch(channel_id, msg)
    return
