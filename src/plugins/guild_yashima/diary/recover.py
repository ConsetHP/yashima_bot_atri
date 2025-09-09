import json
import re

from datetime import datetime

from nonebot import get_bot
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, ActionFailed
from nonebot_plugin_guild_patch import GuildMessageEvent, GuildChannelRecallNoticeEvent
from nonebot.params import EventMessage
from nonebot.matcher import Matcher
from nonebot.typing import T_State

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
    """发送用户在该频道的最后一次发送的图片的url  TODO: 待重构"""
    # query = (
    #     GuildMessageRecord.select()
    #     .where(
    #         (GuildMessageRecord.channel.channel_id == event.channel_id)
    #         & (GuildMessageRecord.user.user_id == event.get_user_id())
    #         & (GuildMessageRecord.image.is_null(False))
    #     )
    #     .order_by(GuildMessageRecord.recv_time.desc())
    #     .first()
    # )

    # if query:
    #     to_send: list[Message] = []
    #     img_url = Message(MessageSegment.text(f"{query.content}"))
    #     head_banner = Message(
    #         MessageSegment.text("◤◢◤◢◤◢◤◢◤◢◤◢\n🈲  banned by tencent 🈲\n◤◢◤◢◤◢◤◢◤◢◤◢")
    #     )
    #     preview_msg = Message(
    #         MessageSegment.text("🏞️ 画像のプレヴュー")
    #         + MessageSegment.image(await build_preview_image(str(query.content)))
    #     )
    #     hint_msg = Message(
    #         MessageSegment.text(
    #             "🔗 画像のURLはこちらです：\n（如果出现'已停止访问该网页'，请手动复制 URL 到正规浏览器中打开）"
    #         )
    #     )
    #     foot_banner = Message(
    #         MessageSegment.text(
    #             f"◤◢◤◢◤◢◤◢◤◢◤◢\n🍀tap URL above to see🍀\n◤◢◤◢◤◢◤◢◤◢◤◢\n{atri.modal_particle}、{atri.proud}"
    #         )
    #     )
    #     to_send.extend([head_banner, preview_msg, hint_msg, img_url, foot_banner])
    #     await send_msgs(event.channel_id, to_send)
    # else:
    #     to_send = f"{atri.loading}。データが見つかりません"
    #     await send_msgs(event.channel_id, to_send)


def extract_cq_image_url(cq_code: str) -> str | None:
    """
    从 [CQ:image,...,url=xxx] 中提取 url 内容
    """
    match = re.search(r"url=([^,\]]+)", cq_code)
    if match:
        return match.group(1)
    return None


def do_notify_system_recalling(notify_recalling: type[Matcher]):
    @notify_recalling.handle()
    async def notify_system_recalling(
        event: GuildChannelRecallNoticeEvent, state: T_State
    ):
        """主动提醒系统撤回消息行为"""
        # 检查被撤回消息的发送者
        try:
            msg = await get_bot(get_config()["general"]["bot_id"]).get_guild_msg(
                message_id=event.message_id, no_cache=False
            )
            logger.info(f"频道用户 {msg['sender']['nickname']} 的消息被系统撤回")
            msg_content: str = msg["message"]
            logger.info(f"消息内容：{msg_content}")

            # 被撤回的是机器人自己的消息则不提醒
            if msg["sender"]["tiny_id"] == str(get_config()["general"]["bot_tiny_id"]):
                await notify_recalling.finish()
        except ActionFailed as af:
            logger.warning(f"撤回消息详情获取错误：{af}")

            # 确保不在半夜刷屏
            current_time = datetime.now()
            if is_silent_period(current_time):
                await notify_recalling.finish()

        # 不在测试频道提醒
        if str(event.channel_id) == get_config()["debug"]["test_channel_id"]:
            await notify_recalling.finish()
        await send_msgs(event.channel_id, "藤子的大手 撤回了一条消息")
        await notify_recalling.finish()


def is_silent_period(current_time: datetime) -> bool:
    """是否是藤子批量撤回时间段"""
    silent_start = current_time.replace(hour=0, minute=0, second=1, microsecond=0)
    silent_end = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
    if current_time >= silent_start and current_time <= silent_end:
        return True
    return False


async def is_system_operator_recall(event: GuildChannelRecallNoticeEvent) -> bool:
    return event.user_id == 0
