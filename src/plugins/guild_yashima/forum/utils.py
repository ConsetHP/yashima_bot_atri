import re
from markdown import markdown
from typing import Annotated, Union

from PIL.Image import Image as PILImage
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, EventPlainText
from nonebot.adapters.qq import (
    MessageCreateEvent,
    ForumPostCreateEvent,
    ForumThreadUpdateEvent,
    Bot,
    ActionFailed,
)
from nonebot.adapters.qq.models import ChannelType, Channel

from ..http import http_client
from ..image import pic_url_to_image
from ..utils import get_config


def gen_handle_cancel(matcher: type[Matcher], message: str):
    async def _handle_cancel(text: Annotated[str, EventPlainText()]):
        if text == "取消":
            await matcher.finish(message)

    return Depends(_handle_cancel)


def get_event_img(event: MessageCreateEvent) -> list[str] | None:
    if msg := event.get_message():
        return [
            per_msg.data["url"]
            for per_msg in msg
            if per_msg.type in ["image", "attachment"]
        ]
    else:
        return None


def generate_thread_title(text: str) -> str:
    """根据投稿内容生成帖子标题"""
    match = re.search(r"^(.*?)\n", text)

    if match:
        text = match.group(1)
        return f"{text[:15]}..." if len(text) > 15 else text
    else:
        return f"{text[:15]}..." if len(text) > 15 else text


async def get_user_nick(
    bot: Bot, event: Union[MessageCreateEvent, ForumPostCreateEvent]
):
    """获取频道用户昵称"""
    nick_name = "未知昵称"
    try:
        if isinstance(event, ForumPostCreateEvent):
            nick_name = (
                await bot.get_member(guild_id=event.guild_id, user_id=event.author_id)
            ).nick
        elif isinstance(event, MessageCreateEvent):
            nick_name = (
                await bot.get_member(
                    guild_id=event.guild_id, user_id=event.get_user_id()
                )
            ).nick
    except ActionFailed as af:
        logger.warning(f"无法获取昵称：{af}，用户id：{event.get_user_id()}")
    return nick_name


async def get_channel_name(
    bot: Bot, event: Union[MessageCreateEvent, ForumPostCreateEvent]
):
    """获取子频道名称"""
    channel_name = "未知子频道"
    try:
        channel_name = (await bot.get_channel(channel_id=event.channel_id)).name
    except ActionFailed as af:
        logger.warning(f"无法获取昵称：{af}，用户id：{event.get_user_id()}")
    return channel_name


async def get_thread_channels(bot: Bot, event: MessageCreateEvent):
    """获取所有帖子子频道"""
    raw_channels = await bot.get_channels(guild_id=event.guild_id)
    sorted_channels = sorted(raw_channels, key=lambda x: x.name)
    channels: list[Channel] = []
    for per_channel in sorted_channels:
        if per_channel.type == 10007 or per_channel.type == ChannelType.DISCUSSION:
            channels.append(per_channel)
    thread_channels: dict[str, str] = {}
    for per_channel in channels:
        thread_channels[per_channel.name] = per_channel.id
    return thread_channels


async def get_img_size(img_url: str) -> tuple[int, int]:
    """下载并获取图片宽度和高度"""
    img: PILImage = await pic_url_to_image(img_url, http_client())
    return img.size


def markdown_to_html(text: str, source: tuple[str, str] | None = None) -> str:
    """将 markdown 格式转换为频道帖子支持的 html 格式"""
    html_text = markdown(text, extensions=["nl2br"], output_format="html")
    html_text = html_text.replace("\n", "")
    html_text = f'<!DOCTYPE html><html lang="zh-CN"><body>{html_text}'
    if source:
        channel_id, user_id = source
        html_text += f'<p align="center">{number_escape(channel_id)} | {number_escape(user_id)}</p>'
    html_text += "</body></html>"
    return html_text


def number_escape(raw_num: str) -> str:
    """处理文本中的数字，防止吞帖"""
    upper_case_chinese_nums = {
        "1": "壹",
        "2": "贰",
        "3": "叁",
        "4": "肆",
        "5": "伍",
        "6": "陆",
        "7": "柒",
        "8": "捌",
        "9": "玖",
        "0": "零",
    }
    for num, escaped in upper_case_chinese_nums.items():
        escaped_num = raw_num.replace(num, escaped)
    return escaped_num


def replace_qq_emoji(text: str) -> str:
    """替换文本中的qq表情"""
    return re.sub(r"<emoji:\d+>", "[表情]", text)


def is_bot_thread(event: ForumThreadUpdateEvent) -> bool:
    return event.author_id == get_config()["general"]["official_bot_id"]
