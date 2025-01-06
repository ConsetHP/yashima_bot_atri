from abc import ABC, abstractmethod
from dataclasses import dataclass

from nonebot.adapters.onebot.v11 import MessageSegment, Message

from ..utils import text_to_image
from ..utils.utils import get_config


@dataclass(kw_only=True)
class AbstractPost(ABC):
    compress: bool = False
    extra_msg: list[Message] | None = None

    @abstractmethod
    async def generate(self) -> list[MessageSegment]:
        "Generate MessageSegmentFactory list from this instance"
        ...

    async def generate_messages(self) -> list[Message]:
        "really call to generate messages"
        msg_segments = await self.generate()
        msg_segments = await self.message_segments_process(msg_segments)
        msgs = await self.message_process(msg_segments)
        return msgs

    async def message_segments_process(self, msg_segments: list[MessageSegment]) -> list[MessageSegment]:
        "检查消息是否需要转换成图片并处理"

        async def convert(msg: str) -> MessageSegment:
            if isinstance(msg, str):
                return await text_to_image(msg)
            else:
                return msg

        if get_config()["subscribe"]["text_to_image"]:
            return [await convert(msg) for msg in msg_segments]

        return msg_segments

    async def message_process(self, msg_segments: list[MessageSegment]) -> list[Message]:
        "检查消息是否需要压缩成一条消息并处理"
        if self.compress:
            msgs = [Message(msg_segments)]
        else:
            msgs = [Message(msg_segment) for msg_segment in msg_segments]

        if self.extra_msg:
            msgs.extend(self.extra_msg)

        return msgs
