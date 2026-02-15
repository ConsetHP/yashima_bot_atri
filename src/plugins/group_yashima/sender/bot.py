"""
简化版 nonebot saa，参考 https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere
Question:
为什么不直接用 saa
Answer:
saa 不支持 cqhttp 的频道API
"""

from typing import Callable, Awaitable

from nonebot import get_bot
from nonebot.adapters import Bot, Message

from .model import SendTarget, AdapterName


Sender = Callable[[Bot, SendTarget, Message], Awaitable[None]]


class BotSelecter:
    sender: dict[AdapterName, Sender] = {}

    @classmethod
    def register_sender(cls, adapter: AdapterName):
        def wrapper(func: Sender):
            cls.sender[adapter] = func
            return func

        return wrapper

    async def send_to(self, target: SendTarget, msg: Message):
        bot = get_bot(target.bot_id)
        adapter = AdapterName(bot.adapter.get_name())
        if sender := self.__class__.sender.get(adapter):
            await sender(bot, target, msg)
            return
        raise RuntimeError("No sender registered")
