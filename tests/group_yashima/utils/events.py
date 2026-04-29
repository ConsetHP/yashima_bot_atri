from typing import TYPE_CHECKING, Literal, Optional

from nonebot.compat import PYDANTIC_V2, ConfigDict

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent


def fake_group_message_event(**field) -> "GroupMessageEvent":
    from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
    from nonebot.adapters.onebot.v11.event import Sender, Reply
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=GroupMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "normal"
        user_id: int = 10
        message_type: Literal["group"] = "group"
        group_id: int = 10000
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(
            card="",
            nickname="test",
            role="member",
        )
        to_me: bool = False
        reply: Optional[Reply] = None

        if PYDANTIC_V2:
            model_config = ConfigDict(extra="forbid")  # type: ignore
        else:

            class Config:  # type: ignore
                extra = "forbid"

    return FakeEvent(**field)
