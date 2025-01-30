from ast import literal_eval

from nonebot.matcher import Matcher
from nonebot.params import Arg, EventPlainText  # noqa: F401
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Message
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..db_config import config
from ..platform import platform_manager  # noqa: F401
from ..types import Category  # noqa: F401
from ..utils import parse_text

from .utils import ensure_channel_id, gen_handle_cancel


def do_del_sub(del_sub: type[Matcher]):
    handle_cancel = gen_handle_cancel(del_sub, "删除中止")

    del_sub.handle()(ensure_channel_id(del_sub))

    @del_sub.handle()
    async def send_list(event: GuildMessageEvent, state: T_State):
        channel_info = event.channel_id
        sub_list = await config.list_subscribe(channel_info)
        if not sub_list:
            await del_sub.finish("暂无已订阅账号\n请使用“添加订阅”命令添加订阅")
        res = "当前子频道订阅的帐号为：\n"
        state["sub_table"] = {}
        for index, sub in enumerate(sub_list, 1):
            state["sub_table"][index] = {
                "platform_name": sub.target.platform_name,
                "target": sub.target.target,
            }
            res += f"{index}. 【{sub.target.platform_name}】 {sub.target.target_name} ({sub.target.target})\n"
            if platform := platform_manager.get(sub.target.platform_name):
                if platform.categories:
                    res += " [{}]".format(
                        ", ".join(
                            platform.categories[Category(x)]
                            for x in literal_eval(sub.categories)
                        )
                    )
                if platform.enable_tag:
                    res += " {}".format(", ".join(literal_eval(sub.tags)))
            else:
                res += f" （平台 {sub.target.platform_name} 已失效，请删除此订阅）"
            if res[-1] != "\n":
                res += "\n"
        res += "请输入要删除的订阅的序号\n输入'取消'中止"
        await del_sub.send(Message(await parse_text(res)))

    @del_sub.receive(parameterless=[handle_cancel])
    async def do_del(
        event: GuildMessageEvent,
        state: T_State,
        index_str: str = EventPlainText(),
    ):
        channel_info = event.channel_id
        try:
            index = int(index_str)
            await config.del_subscribe(channel_info, **state["sub_table"][index])
        except Exception as err:
            await del_sub.reject(f"删除错误：{err}")
        else:
            await del_sub.finish("删除成功")
