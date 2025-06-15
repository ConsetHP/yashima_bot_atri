from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.adapters.qq import MessageCreateEvent as GuildMessageEvent
from nonebot.params import EventMessage

from .db_model import QQGuildImgRecord, QQGuildMessageRecord


async def save_guild_img_url_handle(
    event: GuildMessageEvent, message: Message = EventMessage()
):
    """保存所有频道的图片url"""
    if message.count("image") == 0:
        return

    try:
        for msg in event.get_message():
            if msg.type in ["image", "attachment"]:
                url = (
                    msg.data["url"]
                    if msg.data["url"].startswith("http")
                    else f"https://{msg.data['url']}"
                )
                model = QQGuildImgRecord(
                    channel_id=event.channel_id,
                    user_id=event.get_user_id(),
                    content=url,
                )
                model.save()
    except Exception as e:
        logger.warning(f"出现错误：{e}")


async def save_recv_guild_msg_handle(event: GuildMessageEvent):
    """保存所有频道文本消息"""
    msg = event.get_plaintext()

    if len(msg) > 1000 or msg == "":
        return
    model = QQGuildMessageRecord(
        channel_id=event.channel_id, user_id=event.get_user_id(), content=msg
    )
    model.save()
