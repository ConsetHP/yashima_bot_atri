import json

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from nonebot.adapters import Message, MessageSegment, Bot
from nonebot.log import logger

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11.event import Reply


class ParserFactory:
    _parsers: dict[int, "MessageParser"] = {}
    _message_data: Optional[dict]
    """消息data反序列化缓存，防止json重复解析"""

    @classmethod
    def _sort_parsers(cls):
        cls._parsers = dict(
            sorted(cls._parsers.items(), key=lambda x: x[0], reverse=True)
        )

    @classmethod
    def register(cls, parser: type["MessageParser"], weight: int):
        if issubclass(parser, MessageParser):
            cls._parsers[weight] = parser()
            cls._sort_parsers()

    @classmethod
    async def get_content(
        cls, message: Message, bot: Bot, reply: Optional["Reply"] = None
    ) -> Optional[str]:
        for per_parser in cls._parsers.values():
            if per_parser.is_match(message):
                # TODO: 处理Reply
                logger.info(f"将使用：{type(per_parser).__name__}解析")
                result = await per_parser.parse(message, bot)
                cls._message_data = None
                return result
        return None


class MessageParser(ABC):
    _instances = {}
    # 权重，数值越高越先匹配
    weight: int

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        ParserFactory.register(cls, cls.weight)

    @abstractmethod
    def is_match(self, message: Message) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def parse(self, message: Message, bot: Bot) -> str:
        raise NotImplementedError

    def serialize_msg(self, msgs: list[dict]) -> str:
        return json.dumps(msgs, ensure_ascii=False)

    def get_data_or_update(self, message: Message) -> dict:
        if not ParserFactory._message_data:
            deserialized = json.loads(message[0].data["data"])
            ParserFactory._message_data = deserialized
        else:
            deserialized = ParserFactory._message_data
        return deserialized


class StandardMessageParser(MessageParser):
    """普通单条消息"""

    weight = 1

    def is_match(self, message: Message) -> bool:
        return len(message) == 1

    async def parse(self, message: Message, bot: Bot) -> str:
        segment: MessageSegment = message[0]
        msg = [{"type": segment.type, "data": segment.data}]
        return self.serialize_msg(msg)


class MultiSegmentParser(MessageParser):
    """图文/at/表情等混排消息"""

    weight = 80

    def is_match(self, message: Message) -> bool:
        return len(message) > 1

    async def parse(self, message: Message, bot: Bot) -> str:
        messages: list[dict] = []
        for per_segment in message:
            messages.append({"type": per_segment.type, "data": per_segment.data})
        return self.serialize_msg(messages)


class MiniAppParser(MessageParser):
    """小程序消息"""

    weight = 90

    def is_match(self, message: Message) -> bool:
        if len(message) != 1:
            return False
        if message[0].type != "json":
            return False
        deserialized = self.get_data_or_update(message)
        return deserialized.get("app") != "com.tencent.multimsg"

    async def parse(self, message: Message, bot: Bot) -> str:
        deserialized = self.get_data_or_update(message)
        msg = [{"type": "json", "data": deserialized}]
        return self.serialize_msg(msg)


class ForwardMessageParser(MessageParser):
    """合并转发消息"""

    weight = 100

    def is_match(self, message: Message) -> bool:
        if len(message) != 1:
            return False
        if message[0].type != "json":
            return False
        deserialized = self.get_data_or_update(message)
        return deserialized.get("app") == "com.tencent.multimsg"

    async def parse(self, message: Message, bot: Bot) -> str:
        deserialized = self.get_data_or_update(message)
        res_id: str = deserialized["meta"]["detail"]["resid"]
        resp: dict = await bot.get_forward_msg(id=res_id)
        return self.serialize_msg([resp])
