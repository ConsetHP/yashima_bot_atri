"""
消息存储
有参考 https://github.com/he0119/nonebot-plugin-wordcloud
"""

from datetime import timedelta, datetime

from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.matcher import Matcher
from nonebot.plugin import on_command, require
from nonebot.params import CommandArg

require("nonebot_plugin_guild_patch")

from nonebot_plugin_guild_patch import GuildMessageEvent  # noqa: E402

from . import scheduler as scheduler  # noqa: E402
from .analyzer import get_wordcloud_img  # noqa: E402
from ..character import atri  # noqa: E402
from ..diary.database.operator import get_messages_by_channel_in_period  # noqa: E402
from ..utils import at_user, is_admin_user  # noqa: E402
from ..send import send_msgs  # noqa: E402


yesterday_wordcloud_matcher = on_command("昨日词云", permission=is_admin_user)


@yesterday_wordcloud_matcher.handle()
async def yesterday_wordcloud_handle(
    _: Matcher, event: GuildMessageEvent, args: Message = CommandArg()
):
    yesterday = datetime.now() - timedelta(days=1)
    start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    channel_id = args.extract_plain_text()
    progress_msg = f"ワードクラウドをジェネレートしますね。{atri.loading}"
    await send_msgs(event.channel_id, progress_msg)

    resp = "指定されたチャンネル"
    if not channel_id:
        channel_id = event.channel_id
        resp = "このチャンネル"
    else:
        channel_id = int(channel_id)
    messages = get_messages_by_channel_in_period(channel_id, start_time, end_time)
    image = await get_wordcloud_img(messages)
    if image:
        msg = MessageSegment.text(
            f"{atri.modal_particle}、{resp}のワードクラウドがジェネレートしました🎉、{atri.proud}"
        ) + MessageSegment.image(image)
        await send_msgs(event.channel_id, msg)
    else:
        msg = at_user(event) + MessageSegment.text(
            f"{resp}のチャットレコードが足りないようです"
        )
        await send_msgs(event.channel_id, msg)
