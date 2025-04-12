from nonebot.typing import T_State
from nonebot.adapters.qq.models import Message

from .types import Reply, Upload, Channel, UploadInfo, Content
from .utils import replace_qq_emoji


def do_parse(state: T_State) -> Upload:
    """将 state 中的信息组装成 Upload"""
    if state["reply"]:
        msg_reply: Message = state["reply"]
        reply_text = replace_qq_emoji(msg_reply.content) if msg_reply.content else None
        reply_imgs = (
            [per_attach.url for per_attach in msg_reply.attachments]
            if msg_reply.attachments
            else None
        )
        reply_content = Content(text=reply_text, images=reply_imgs)
        reply = Reply(author=msg_reply.author, content=reply_content)
    else:
        reply = None
    text = state["text"]
    imgs = state["imgs"]
    if reply and not text and not imgs:
        text = ""

    content = Content(text=text, images=imgs)
    info = UploadInfo(
        source_channel=Channel(
            id=state["source_channel_id"], name=state["source_channel_name"]
        ),
        target_channel=Channel(
            id=state["target_channel_id"], name=state["target_channel_name"]
        ),
    )
    return Upload(author=state["author"], content=content, info=info, reply=reply)
