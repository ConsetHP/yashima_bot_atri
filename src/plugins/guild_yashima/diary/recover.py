import json

from datetime import datetime

from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_guild_patch import GuildMessageEvent, GuildChannelRecallNoticeEvent
from nonebot.params import EventMessage
from nonebot.matcher import Matcher

from .image import build_preview_image
from .db_model import GuildImgRecord
from .utils import parse_tencent_link_card
from ..utils import get_config
from ..http import process_url
from ..character import atri
from ..send import send_msgs


async def resend_pc_unreadable_msg_handle(
    _: Matcher, event: GuildMessageEvent, message: Message = EventMessage()
):
    """解析PC不可读消息并转换发送"""
    if message.count("json") == 0:
        return

    segment = message["json", 0]
    json_data = json.loads(segment.get("data").get("data"))

    link, title = parse_tencent_link_card(json_data)

    if not link or not link.startswith("http"):
        logger.warning(f"链接异常：{link}")
        return
    if len(title) > 50:
        title = title[:50] + "…"
    elif not title:
        title = f"{atri.error_occurred}：タイトルを解析することができません"

    # 处理url防止qq二度解析（在http后添加一个零宽空格）
    link = process_url(link)

    if len(link) > 300:
        logger.warning(f"链接过长，将不会发送：{link}")
        return
    to_send: list[Message] = []
    hint_msg = Message(MessageSegment.text("🔽 URLはこちらです："))
    content = Message(MessageSegment.text(f"{title}\n{link}"))
    footer = Message(MessageSegment.text(f"{atri.modal_particle}、{atri.fuck_tencent}"))
    to_send.extend([hint_msg, content, footer])
    await send_msgs(event.channel_id, to_send)


async def resend_system_recalled_img_handle(_: Matcher, event: GuildMessageEvent):
    """发送用户在该频道的最后一次发送的图片的url"""
    query = (
        GuildImgRecord.select()
        .where(
            (GuildImgRecord.channel_id == event.channel_id)
            & (GuildImgRecord.user_id == event.get_user_id())
        )
        .order_by(GuildImgRecord.recv_time.desc())
        .first()
    )

    if query:
        to_send: list[Message] = []
        img_url = Message(MessageSegment.text(f"{query.content}"))
        head_banner = Message(
            MessageSegment.text("◤◢◤◢◤◢◤◢◤◢◤◢\n🈲  banned by tencent 🈲\n◤◢◤◢◤◢◤◢◤◢◤◢")
        )
        preview_msg = Message(
            MessageSegment.text("🏞️ 画像のプレヴュー")
            + MessageSegment.image(await build_preview_image(str(query.content)))
        )
        hint_msg = Message(
            MessageSegment.text(
                "🔗 画像のURLはこちらです：\n（如果出现'已停止访问该网页'，请手动复制 URL 到正规浏览器中打开）"
            )
        )
        foot_banner = Message(
            MessageSegment.text(
                f"◤◢◤◢◤◢◤◢◤◢◤◢\n🍀tap URL above to see🍀\n◤◢◤◢◤◢◤◢◤◢◤◢\n{atri.modal_particle}、{atri.proud}"
            )
        )
        to_send.extend([head_banner, preview_msg, hint_msg, img_url, foot_banner])
        await send_msgs(event.channel_id, to_send)
    else:
        to_send = f"{atri.loading}。データが見つかりません"
        await send_msgs(event.channel_id, to_send)


async def notify_system_recalling_handle(
    matcher: Matcher, event: GuildChannelRecallNoticeEvent
):
    """主动提醒吞消息行为"""
    if str(event.channel_id) == get_config()["debug"]["test_channel_id"]:
        await matcher.finish()

    # 凌晨暂时静默，避开藤子撤回时间段
    today = datetime.now()
    silent_start = today.replace(hour=0, minute=0, second=1, microsecond=0)
    silent_end = today.replace(hour=5, minute=0, second=0, microsecond=0)
    if today >= silent_start and today <= silent_end:
        await matcher.finish()

    await send_msgs(event.channel_id, "藤子的大手 撤回了一条消息")


async def is_system_operator_recall(event: GuildChannelRecallNoticeEvent) -> bool:
    return event.user_id == 0
