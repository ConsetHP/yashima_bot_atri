"""
消息发送队列
参考 https://github.com/MountainDash/nonebot-bison
"""

import asyncio
import traceback
from collections import deque

from nonebot.adapters import Message
from nonebot.log import logger

from .model import SendTarget
from .bot import BotSelecter
from ..config import get_config

QUEUE: deque[tuple[SendTarget, Message, int]] = deque()

MESSAGE_SEND_INTERVAL = get_config().sender.message_send_interval
MESSAGE_SEND_RETRY = get_config().sender.message_send_retry

_MESSAGE_DISPATCH_TASKS: set[asyncio.Task] = set()


async def _do_send(target: SendTarget, msg: Message):
    await BotSelecter().send_to(target, msg)


async def do_send_msgs():
    """处理队列中的消息发送任务"""
    if not QUEUE:
        return
    while True:
        # 先读取队列再pop任务，如果先pop，队列长度变成0，此时加入新任务会导致函数被重复执行
        target, msg, retry_time = QUEUE[0]
        try:
            await _do_send(target, msg)
        except Exception as e:
            await asyncio.sleep(MESSAGE_SEND_INTERVAL)
            QUEUE.popleft()
            if retry_time > 0:
                logger.warning(f"消息发送失败, 剩余重试次数: {retry_time}")
                QUEUE.appendleft((target, msg, retry_time - 1))
            else:
                msg_str = str(msg)
                if len(msg_str) > 100:
                    msg_str = msg_str[:100] + "..."
                logger.warning(f"重试次数耗尽，发送消息错误： {e} {msg_str}")
                traceback.print_exc()
        else:
            # 先sleep后pop，否则会出现上条注释提到的重复执行错误
            await asyncio.sleep(MESSAGE_SEND_INTERVAL)
            QUEUE.popleft()
        finally:
            if not QUEUE:
                return


async def _send_msgs_dispatch(target: SendTarget, msg: Message):
    QUEUE.append((target, msg, MESSAGE_SEND_RETRY))
    # 队列长度在 append 前是 0
    if len(QUEUE) == 1:
        task = asyncio.create_task(do_send_msgs())
        _MESSAGE_DISPATCH_TASKS.add(task)
        task.add_done_callback(_MESSAGE_DISPATCH_TASKS.discard)


async def send_msgs(target: SendTarget, msg: Message):
    """将消息发送任务添加至队列"""
    await _send_msgs_dispatch(target, msg)
