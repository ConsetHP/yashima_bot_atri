import re
from typing import Tuple, List, Optional

from nonebot.log import logger
from nonebot import Bot, get_bot
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.minecraft import (
    Message as MinecraftMessage,
    MessageSegment as MinecraftMessageSegment,
)
from nonebot.adapters.minecraft import (
    Event as MinecraftEvent,
    MessageEvent as MinecraftMessageEvent,
)
from nonebot.adapters.onebot.v11 import ActionFailed
from nonebot.adapters.minecraft.model import (
    TextColor,
    ClickEvent,
    HoverEvent,
    ClickAction,
    HoverAction,
    BaseComponent,
)

from ..send import send_msgs
from ..utils import get_config


CHANNEL_ID: str = get_config()["minecraft"][
    "minecraft_channel_id"
]  # Minecraft 子频道的ID


async def send_mc_msg_to_qq(server_name: str, result: str):
    """向 QQ 客户端发送消息"""
    # 去除 Minecraft 格式化符号
    msg_result = re.sub(r"[&§].", "", result)
    # 添加服务器名前缀
    msg_result = f"[{server_name}] {msg_result}"
    await send_msgs(CHANNEL_ID, msg_result)


async def parse_qq_msg_to_base_model(
    bot: Bot, event: GuildMessageEvent
) -> Tuple[MinecraftMessage, str]:
    """
    解析 QQ 消息，转为 WebSocketBody 模型
    :param bot: 聊天平台Bot实例
    :param event: 所有事件
    :return: Message
    """

    message_list = MinecraftMessage()
    log_text = ""

    # 消息发送者昵称
    sender_nickname_text = await __get_group_or_nick_name(
        bot, event, str(event.get_user_id())
    )
    message_list.append(
        MinecraftMessageSegment.text(
            text=f" {sender_nickname_text} ", color=TextColor.GREEN
        )
    )
    log_text += sender_nickname_text

    # 添加聊天消息修饰（xxx 说：）
    if accent := get_config()["minecraft"]["minecraft_message_accent"]:
        message_list.append(MinecraftMessageSegment.text(text=accent))
        log_text += accent

    # 消息内容
    temp_message_list, msg_log_text = await __get_common_qq_msg_parsing(bot, event)
    temp_message_list: List[MinecraftMessageSegment]
    log_text += msg_log_text

    message_list += MinecraftMessage(temp_message_list)

    return message_list, log_text


async def __get_common_qq_msg_parsing(bot: Bot, event: GuildMessageEvent):
    """
    获取QQ消息解析后的消息列表和日志文本
    :param bot: Bot对象
    :param event: 事件对象
    :param rcon_mode: 是否为RCON模式
    :return: 消息列表和日志文本
    """
    log_text = ""

    message_list = []

    # 消息内容
    for msg in event.get_message():
        click_event = None
        hover_event = None
        temp_color = None
        if msg.type == "text":
            temp_text = msg.data["text"].replace("\r", "").replace("\n", "\n * ") + " "
            log_text += temp_text
            message_list.append(temp_text)
            continue

        elif msg.type in ["image", "attachment"]:
            temp_text = "[图片]"
            temp_color = TextColor.LIGHT_PURPLE
            img_url = (
                msg.data["url"]
                if msg.data["url"].startswith("http")
                else f"https://{msg.data['url']}"
            )
            # 这俩 event 有 bug ,在 MinecraftMessageSegment 里加入这俩玩意会导致鹊桥接口超时
            # hover_event, click_event = __get_action_event_component(img_url, temp_text)
        elif msg.type == "video":
            temp_text = "[视频]"
            temp_color = TextColor.LIGHT_PURPLE
            img_url = (
                msg.data["url"]
                if msg.data["url"].startswith("http")
                else f"https://{msg.data['url']}"
            )
            # hover_event, click_event = __get_action_event_component(img_url, temp_text)
        elif msg.type == "share":
            temp_text = "[分享]"
            temp_color = TextColor.GOLD
            img_url = (  # noqa: F841
                msg.data["url"]
                if msg.data["url"].startswith("http")
                else f"https://{msg.data['url']}"
            )
            # hover_event, click_event = __get_action_event_component(img_url, temp_text)

        # @用户
        elif msg.type == "at":
            if msg.data["qq"] == "all":
                temp_text = "@全体成员"
            else:
                temp_text = (
                    f"@{await __get_group_or_nick_name(bot, event, msg.data['qq'])}"
                )
            temp_color = TextColor.GREEN

        # @子频道
        elif msg.type == "mention_channel":
            temp_text = f"@{(await bot.get_channel(channel_id=event.channel_id)).name}"
            temp_color = TextColor.GREEN

        # @全体成员
        elif msg.type == "mention_everyone":
            temp_text = "@全体成员"
            temp_color = TextColor.GREEN

        elif msg.type in ["face", "emoji"]:
            temp_text = "[表情]"
            temp_color = TextColor.GREEN

        elif msg.type == "record":
            temp_text = "[语音]"
            temp_color = TextColor.GOLD
        else:
            temp_text = "[未知消息类型]"

        temp_text = temp_text.strip() + " "

        log_text += temp_text

        temp_component = MinecraftMessageSegment.text(
            text=temp_text,
            color=temp_color,
            hover_event=hover_event,
            click_event=click_event,
        )
        message_list.append(temp_component)

    return message_list, log_text


def __get_action_event_component(img_url: str, temp_text: str):
    """
    获取HoverEvent和ClickEvent组件
    :param img_url: 图片链接
    :param temp_text: 文本
    :return: HoverEvent和ClickEvent组件
    """
    temp_text = temp_text.replace("[", "[查看")
    hover_event = HoverEvent(
        action=HoverAction.SHOW_TEXT,
        text=[BaseComponent(text=temp_text, color=TextColor.DARK_PURPLE)],
    )
    click_event = ClickEvent(action=ClickAction.OPEN_URL, value=img_url)
    return hover_event, click_event


async def __get_group_or_nick_name(
    bot: Bot, event: GuildMessageEvent, user_id: Optional[str] = None
) -> str:
    """
    获取频道名或者频道用户昵称
    :param bot: 平台Bot实例
    :param event: 事件
    :param user_id: 用户ID
    :return: 昵称
    """
    temp_text = "未知昵称" if user_id is None else "[未知频道]"
    try:
        if isinstance(event, GuildMessageEvent) and isinstance(bot, Bot):
            if user_id:
                if event.user_id == user_id:
                    temp_text = event.sender.nickname
                else:
                    temp_text = (
                        await bot.get_guild_member_profile(
                            guild_id=event.guild_id, user_id=user_id
                        )
                    )["nickname"]
            else:
                temp_text = ""
                for per_channel in await bot.get_guild_channel_list(
                    guild_id=event.guild_id, no_cache=True
                ):
                    if str(event.channel_id) == per_channel["channel_id"]:
                        channel_name = per_channel["channel_name"]
                        temp_text = f"[{channel_name}]"
                        break
    except ActionFailed as af:
        logger.warning(f"无法获取昵称：{af}")
    finally:
        return temp_text


async def send_qq_msg_to_mc(server_name: str, message: str):
    """向 Minecraft 服务器发送消息"""
    mc_bot = get_bot(server_name)
    if not mc_bot:
        logger.info(f"服务器 {server_name} 未连接")
        return
    await mc_bot.send_msg(message=message)


def minecraft_channel_id() -> str:
    return get_config()["minecraft"]["minecraft_channel_id"]


def is_minecraft_channel(event: GuildMessageEvent) -> bool:
    return minecraft_channel_id() == str(event.channel_id)


def mc_msg_rule(event: MinecraftEvent):
    if isinstance(event, MinecraftMessageEvent):
        if blacklist_prefix := get_config()["minecraft"]["blacklist_mc_message"]:
            return not any(
                word in str(event.get_message()) for word in blacklist_prefix
            )
    return event.server_name == get_config()["minecraft"]["server_name"]
