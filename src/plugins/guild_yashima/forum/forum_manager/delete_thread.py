from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters import MessageTemplate
from nonebot.params import ArgPlainText
from nonebot.adapters.qq import (
    Bot,
    MessageCreateEvent,
    ActionFailed,
)
from nonebot.typing import T_State

from ..database.operator import database, UserNotFoundError, ThreadNotFoundError


def do_delete_thread(delete_thread: type[Matcher]):
    @delete_thread.handle()
    async def prepare_confirm(event: MessageCreateEvent, state: T_State):
        try:
            debug = False
            user_id = event.get_user_id()
            thread = database.get_last_thread(user_id)
        except UserNotFoundError:
            await delete_thread.finish(
                "❌ 帖子记录不存在，仅可撤回自己使用'/一键发帖'发送的帖子"
            )
        except ThreadNotFoundError:
            # 有时帖子需要审核几分钟才会上报FORUM_THREAD_UPDATE，用户投稿帖子后迅速撤回帖子就可能触发
            if database.thread_is_just_sent(user_id):
                await delete_thread.finish("⏳ 刚刚投稿的帖子正在在审核中，请稍后再试")
            else:
                await delete_thread.send(
                    "⏳ 你要撤回的帖子可能仍在审核中（或者被安全打击），请稍后再试，([调试用]或发送帖子子频道id和帖子id)"
                )
                debug = True
                state["_prompt"] = "📝 输入'确认'以确认撤回 | '取消'以取消撤回"
        except Exception as ex:
            logger.warning(ex)
            await delete_thread.finish("🆖 出错了，请联系bot管理员")
        else:
            if not debug:
                state["thread_channel_id"] = str(thread.thread_channel_id)
                state["thread_id"] = thread.thread_id
            else:
                state["thread_channel_id"] = ""
                state["thread_id"] = ""
            prompt = f"🚨 即将撤回帖子【{thread.title}】\n✨ 如果需要撤回更早的帖子，请联系管理手动处理"
            if database.thread_is_just_sent(user_id):
                prompt += "\n⏳ 看起来你刚才投稿了帖子，如果即将撤回的帖子不是刚才投稿的帖子，说明帖子正在审核中，可以等一会再尝试撤回哦"
            prompt += "\n📝 输入'确认'以确认撤回 | '取消'以取消撤回"
            state["_prompt"] = prompt

    @delete_thread.got("confirm", MessageTemplate("{_prompt}"))
    async def got_confirm(
        bot: Bot,
        event: MessageCreateEvent,
        state: T_State,
        confirm: str = ArgPlainText(),
    ):
        if confirm in ["确认", "确认撤回"]:
            try:
                database.del_last_thread(event.get_user_id())
                await bot.delete_thread(
                    channel_id=state["thread_channel_id"], thread_id=state["thread_id"]
                )
            except ActionFailed as af:
                if af.code == 11264:
                    await delete_thread.finish(
                        "🆖 请在 机器人-权限设置中启用【子频道的帖子删除】"
                    )
                elif af.code == 503013:
                    # af.message是‘服务器内部错误’，藤子的 open_api 有bug，正常应该返回 503012
                    await delete_thread.finish("🆖 帖子不存在，可能已经被管理删除了")
                else:
                    print(af.code)
                    await delete_thread.finish(
                        af.message if af.message else "🆖 帖子撤回失败，请联系bot管理员"
                    )
            except Exception as ex:
                logger.warning(ex)
                await delete_thread.finish("🆖 出错了，请联系bot管理员")
            else:
                await delete_thread.finish("🆗 成功撤回")
        elif confirm in ["取消", "取消撤回"]:
            await delete_thread.finish("🆗 已取消")
        else:
            if len(confirm.split()) == 2:
                thread_channel_id = confirm.split()[0]
                thread_id = confirm.split()[1]
                try:
                    database.del_last_thread(event.get_user_id())
                    await bot.delete_thread(
                        channel_id=thread_channel_id, thread_id=thread_id
                    )
                except Exception as ex:
                    logger.warning(ex)
                    await delete_thread.finish(f"🆖 出错了 {ex}")
                else:
                    await delete_thread.finish("🆗 成功撤回")
            else:
                await delete_thread.reject("❌ 格式不正确。要取消撤回，请输入'取消'")
