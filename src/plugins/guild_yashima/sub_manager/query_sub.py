from ast import literal_eval

from nonebot.matcher import Matcher
from nonebot.params import Arg  # noqa: F401
from nonebot.adapters.onebot.v11 import Message
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..db_config import config
from ..platform import platform_manager  # noqa: F401
from ..types import Category  # noqa: F401
from ..utils import parse_text

from .utils import ensure_channel_id


def do_query_sub(query_sub: type[Matcher]):
    query_sub.handle()(ensure_channel_id(query_sub))

    @query_sub.handle()
    async def _(event: GuildMessageEvent):
        sub_list = await config.list_subscribe(event.channel_id)
        if not sub_list:
            await query_sub.finish("暂无已订阅账号\n请使用“添加订阅”命令添加订阅")

        res = "当前子频道订阅的帐号为：\n"
        for sub in sub_list:
            res += f"【{sub.target.platform_name}】 {sub.target.target_name} ({sub.target.target})\n"
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
        await query_sub.finish(Message(await parse_text(res)))
