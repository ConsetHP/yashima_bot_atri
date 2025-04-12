from typing import Annotated

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, EventPlainText, ArgPlainText
from nonebot.adapters import MessageTemplate
from nonebot.adapters.qq import MessageCreateEvent, Bot, ActionFailed
from nonebot.typing import T_State

from ..database.operator import database
from ..utils import get_thread_channels


def gen_handle_cancel(matcher: type[Matcher], message: str):
    async def _handle_cancel(text: Annotated[str, EventPlainText()]):
        if text == "取消":
            await matcher.finish(message)

    return Depends(_handle_cancel)


async def get_sendable_channels(
    matcher: Matcher, bot: Bot, event: MessageCreateEvent
) -> dict[str, str]:
    """获取可发送的帖子区"""
    try:
        sendable_channels: dict[str, str] = await get_thread_channels(bot, event)
        if not sendable_channels:
            await matcher.finish(
                "🆖 没有可用的帖子板块，请联系频道管理员创建一个帖子板块"
            )
    except ActionFailed as af:
        logger.warning(f"获取子频道列表错误：{af}")
        if af.code == 11264:
            await matcher.finish(
                "🆖 请在 机器人-权限设置中启用【获取频道内子频道列表】"
            )
        else:
            await matcher.finish(af.message if af.message else "🆖 无法获取子频道列表")
    return sendable_channels


def do_clean_database(clean_database: type[Matcher]):
    @clean_database.handle()
    async def are_you_sure(_: MessageCreateEvent, state: T_State):
        state["_prompt"] = (
            "◤◢◤◢◤◢◤◢◤◢◤◢\n即将清空所有的帖子记录！！\n◤◢◤◢◤◢◤◢◤◢◤◢\n📝 请输入'I AM CERTAIN WHAT IM DOING'确认清空 | 其他内容则清空取消"
        )

    @clean_database.got("confirm", MessageTemplate("{_prompt}"))
    async def clear_forum_database(
        _: MessageCreateEvent, confirm: str = ArgPlainText()
    ):
        if confirm == "I AM CERTAIN WHAT IM DOING":
            logger.info("开始清空数据库")
            database.clear_db()
            await clean_database.finish("🆗 清空成功")
        else:
            await clean_database.finish("🆗 已取消")
