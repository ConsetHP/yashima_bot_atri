from itertools import groupby
from operator import attrgetter
from typing import Annotated

from nonebot.matcher import Matcher
from nonebot.params import Depends, EventPlainText
from nonebot.typing import T_State
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..database import database
from ..platform import platform_manager
from ..types import Category


common_platform = [
    p.platform_name
    for p in filter(
        lambda platform: platform.enabled and platform.is_common,
        platform_manager.values(),
    )
]


def gen_handle_cancel(matcher: type[Matcher], message: str):
    async def _handle_cancel(text: Annotated[str, EventPlainText()]):
        if text == "取消":
            await matcher.finish(message)

    return Depends(_handle_cancel)


def ensure_channel_id(matcher: type[Matcher]):
    async def _check_channel_id(state: T_State):
        if not state.get("target_channel_id"):
            await matcher.finish(
                "No target_channel_id set, this shouldn't happen, please issue"
            )

    return _check_channel_id


async def set_target_channel_id(event: GuildMessageEvent, state: T_State):
    state["target_channel_id"] = event.channel_id


async def generate_sub_list_text(
    matcher: type[Matcher],
    state: T_State,
    channel_id: int | None = None,
    is_index=False,
):
    """根据配置参数，生产订阅列表文本，同时将订阅信息存入state["sub_table"]"""
    if channel_id:
        sub_list = await database.list_subscribe(channel_id)
    else:
        sub_list = await database.list_subs_with_all_info()
        sub_list = [
            next(group)
            for key, group in groupby(
                sorted(sub_list, key=attrgetter("target_id")),
                key=attrgetter("target_id"),
            )
        ]
    if not sub_list:
        await matcher.finish("暂无已订阅账号\n请使用“添加订阅”命令添加订阅")
    res = "订阅的帐号为：\n"
    state["sub_table"] = {}
    for index, sub in enumerate(sub_list, 1):
        state["sub_table"][index] = {
            "platform_name": sub.target.platform_name,
            "target": sub.target.target,
        }
        res += f"{index} " if is_index else ""
        res += (
            f"{sub.target.platform_name} {sub.target.target_name} {sub.target.target}\n"
        )
        if platform := platform_manager.get(sub.target.platform_name):
            if platform.categories:
                res += (
                    " [{}]".format(
                        ", ".join(
                            platform.categories[Category(x)] for x in sub.categories
                        )
                    )
                    + "\n"
                )
            if platform.enable_tag:
                if sub.tags:
                    res += " {}".format(", ".join(sub.tags)) + "\n"
        else:
            res += f" （平台 {sub.target.platform_name} 已失效，请删除此订阅）"

    return res
