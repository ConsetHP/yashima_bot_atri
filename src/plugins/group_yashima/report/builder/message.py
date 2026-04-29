from abc import ABC, abstractmethod
from typing import Any
from string import Template

from nonebot.adapters.onebot.v11 import Message, MessageSegment


class MessageFactory:
    _processors: dict[str, type["SegmentProcessor"]] = {}

    @classmethod
    def register(cls, processor: type["SegmentProcessor"], msg_type: str):
        if issubclass(processor, "SegmentProcessor"):
            cls._processors[msg_type] = processor

    @classmethod
    def get_processor(cls, msg_type: str) -> "SegmentProcessor":
        return cls._processors.get(msg_type, TextProcessor)()

    @classmethod
    async def process_segment(cls, segment: dict | MessageSegment) -> str:
        if isinstance(segment, MessageSegment):
            processor = cls.get_processor(segment.type)
        else:
            processor = cls.get_processor(segment["type"])

        return await processor.process(segment)

    @classmethod
    async def process_message(
        cls, message: list[dict] | Message, user_name: str
    ) -> str:
        result = [await cls.process_segment(seg) for seg in message]
        # 应该不会有人注入吧
        return Template("$user_name: $content").substitute(
            user_name=user_name, content="".join(result)
        )


class SegmentProcessor(ABC):
    _instances = {}
    _msg_type: str

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        MessageFactory.register(cls, cls._msg_type)

    @abstractmethod
    async def process(self, message: dict | Any) -> str:
        raise NotImplementedError


class AtProcessor(SegmentProcessor):
    """at处理"""

    _msg_type = "at"

    async def process(self, message: dict | MessageSegment) -> str:
        # mentioned_user: str = database.get_user_name(message["data"]["qq"])
        # if not mentioned_user:
        # cqhttp获取，失败则直接使用QQ号尾号
        return ""


class QQFaceProcessor(SegmentProcessor):
    """QQ表情处理"""

    _msg_type = "face"

    async def process(self, message: dict | MessageSegment) -> str:
        # TODO: 解读QQ表情ID
        return ""


class TextProcessor(SegmentProcessor):
    """文字处理"""

    _msg_type = "text"

    async def process(self, message: dict | MessageSegment) -> str:
        if isinstance(message, MessageSegment):
            return message.data["content"]
        return message["data"]["text"]


class ImageProcessor(SegmentProcessor):
    """图片处理"""

    _msg_type = "image"

    # TODO: 尝试在接收图片时OCR内容并缓存结果
    async def process(self, message: dict | MessageSegment) -> str:
        return "[图片]"


class VideoProcessor(SegmentProcessor):
    """视频处理"""

    _msg_type = "video"

    async def process(self, message: dict | MessageSegment) -> str:
        return "[视频]"


class JsonProcessor(SegmentProcessor):
    """小程序卡片处理"""

    _msg_type = "json"

    async def process(self, message: dict | MessageSegment) -> str:
        # json可能存在多个不同的miniapp版本，需要小心
        # title = message["data"]["meta"]["desc"]
        return ""


class ForwardProcessor(SegmentProcessor):
    """合并转发消息处理"""

    _msg_type = "forward"

    def _parse_cq_code(self, message: str) -> Message:
        return Message(message)

    async def process(self, message: dict) -> str:
        raw_msgs = message["messages"]
        messages = [
            await MessageFactory.process_message(
                self._parse_cq_code(per_msg["content"]), per_msg["sender"]["nickname"]
            )
            for per_msg in raw_msgs
        ]
        return "\n".join(messages)
