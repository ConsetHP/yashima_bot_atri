import asyncio
from datetime import datetime

from nonebot import on_command, Bot
from nonebot.adapters import MessageTemplate
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, ArgStr
from nonebot.rule import Rule, to_me
from nonebot.typing import T_State

from .add_sub import do_add_sub
from .del_sub import do_del_sub
from .query_sub import do_query_sub
from .utils import (
    common_platform,
    gen_handle_cancel,
    set_target_channel_id,
)
from ...utils import is_admin_user
from ..database import database
from nonebot_plugin_htmlrender import text_to_pic

_COMMAND_DISPATCH_TASKS: set[asyncio.Task] = set()

add_sub_matcher = on_command(
    "添加订阅",
    permission=is_admin_user,
    block=True,
)
add_sub_matcher.handle()(set_target_channel_id)
do_add_sub(add_sub_matcher)


query_sub_matcher = on_command("查询订阅", block=True)
query_sub_matcher.handle()(set_target_channel_id)
do_query_sub(query_sub_matcher)


del_sub_matcher = on_command(
    "删除订阅",
    permission=is_admin_user,
    block=True,
)

del_sub_matcher.handle()(set_target_channel_id)
do_del_sub(del_sub_matcher)

# debug only，使用完需要重启bot
del_sub_db_matcher = on_command(
    "清空订阅数据库", rule=to_me(), permission=is_admin_user, block=True
)


@del_sub_db_matcher.handle()
async def _():
    await database.clear_db()
    await del_sub_db_matcher.finish("已清空")


channel_manage_matcher = on_command(
    "子频道订阅管理", rule=to_me(), permission=is_admin_user, block=True
)

channel_handle_cancel = gen_handle_cancel(channel_manage_matcher, "已取消")


@channel_manage_matcher.handle()
async def send_group_list(bot: Bot, event: GuildMessageEvent, state: T_State):
    channels = await bot.get_guild_channel_list(guild_id=event.guild_id, no_cache=True)
    res_text = "请选择需要管理的子频道：\n"
    channel_id_idx = {}
    for idx, per_channel in enumerate(channels, 1):
        channel_id_idx[idx] = per_channel["channel_id"]
        res_text += f"{idx}. {per_channel['channel_name']}\n"
    res_text += "请输入左侧序号\n中止操作请输入'取消'"
    if len(res_text) > 300:
        image = await text_to_pic(res_text)
        await channel_manage_matcher.send(MessageSegment.image(image))
    else:
        await channel_manage_matcher.send(res_text)
    state["_prompt"] = res_text
    state["channel_id_idx"] = channel_id_idx


@channel_manage_matcher.got(
    "channel_idx", MessageTemplate("{_prompt}"), [channel_handle_cancel]
)
async def do_choose_channel_id(
    state: T_State, _: GuildMessageEvent, channel_idx: str = ArgPlainText()
):
    channel_id_idx: dict[int, int] = state["channel_id_idx"]
    assert channel_id_idx
    idx = int(channel_idx)
    if idx not in channel_id_idx.keys():
        await channel_manage_matcher.reject("请输入正确序号")
    channel_id = channel_id_idx[idx]
    state["target_channel_id"] = channel_id


@channel_manage_matcher.got(
    "command",
    "请输入需要使用的命令：添加订阅，查询订阅，删除订阅，取消",
    [channel_handle_cancel],
)
async def do_dispatch_command(
    bot: Bot,
    event: GuildMessageEvent,
    state: T_State,
    matcher: Matcher,
    command: str = ArgStr(),
):
    if command not in {"添加订阅", "查询订阅", "删除订阅", "取消"}:
        await channel_manage_matcher.reject("请输入正确的命令")
    permission = await matcher.update_permission(bot, event)
    new_matcher = Matcher.new(
        "message",
        Rule(),
        permission,
        handlers=None,
        temp=True,
        priority=0,
        block=True,
        plugin=matcher.plugin,
        module=matcher.module,
        expire_time=datetime.now(),
        default_state=matcher.state,
        default_type_updater=matcher.__class__._default_type_updater,
        default_permission_updater=matcher.__class__._default_permission_updater,
    )
    if command == "查询订阅":
        do_query_sub(new_matcher)
    elif command == "添加订阅":
        do_add_sub(new_matcher)
    else:
        do_del_sub(new_matcher)
    new_matcher_ins = new_matcher()

    task = asyncio.create_task(new_matcher_ins.run(bot, event, state))
    _COMMAND_DISPATCH_TASKS.add(task)
    task.add_done_callback(_COMMAND_DISPATCH_TASKS.discard)


__all__ = [
    "add_sub_matcher",
    "common_platform",
    "del_sub_matcher",
    "channel_manage_matcher",
    "no_permission_matcher",
    "query_sub_matcher",
]
