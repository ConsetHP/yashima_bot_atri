import asyncio

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.qq import (
    Bot,
    MessageCreateEvent,
    MessageSegment,
    ForumThreadUpdateEvent,
    ActionFailed,
)
from nonebot.adapters.qq.models import RichText
from nonebot.adapters import MessageTemplate, Message
from nonebot.params import ArgPlainText, CommandArg
from nonebot.typing import T_State

from ..config import TIMEOUT_MINUTE, CANCEL_PROMPT
from .utils import gen_handle_cancel, get_sendable_channels
from ..database.operator import database
from ..parse import do_parse
from ..utils import get_event_img, markdown_to_html, get_channel_name


record_lock = asyncio.Lock()


def do_send_thread(send_thread: type[Matcher]):
    channel_handle_cancel = gen_handle_cancel(send_thread, "🆗 已取消")

    @send_thread.handle()
    async def prepare_get_channel_name(
        matcher: Matcher,
        bot: Bot,
        event: MessageCreateEvent,
        state: T_State,
        raw_args: Message = CommandArg(),
    ):
        # if not DEFAULT_CHANNEL_NAME:
        #     send_thread.finish("🆖 机器人配置错误，请联系机器人管理员")
        #     raise Exception("默认帖子区未配置，请检查配置文件")

        state["sendable_channels"] = await get_sendable_channels(
            matcher=send_thread, bot=bot, event=event
        )

        # 是否存在回复内容
        if msg_reply := event.reply:
            state["reply"] = msg_reply
            matcher.set_arg("raw_text", raw_args)
        else:
            state["reply"] = None
        # 是否存在参数
        if raw_args.extract_plain_text():
            matcher.set_arg("raw_text", raw_args)
        # 是否有图片
        if img_urls := get_event_img(event):
            state["imgs"] = img_urls
            matcher.set_arg("raw_text", raw_args)
        else:
            state["imgs"] = None
        res_text = "📝 请输入投稿内容，可附带图片\n"
        res_text += f"⏱️ {TIMEOUT_MINUTE}内有效\n{CANCEL_PROMPT}"
        state["_prompt"] = res_text

    @send_thread.got("raw_text", MessageTemplate("{_prompt}"), [channel_handle_cancel])
    async def got_upload_content(
        _: Matcher,
        event: MessageCreateEvent,
        state: T_State,
        raw_text: str = ArgPlainText(),
    ):
        # # 删除投稿内容中的多余参数
        # args = raw_text.split(" ")
        state["text"] = raw_text
        # 是否有图片
        if img_urls := get_event_img(event):
            state["imgs"] = img_urls
        else:
            state["imgs"] = None

    @send_thread.handle()
    async def prepare_get_target_channel(state: T_State, _: MessageCreateEvent):
        # await send_thread.send(
        #     MessageSegment.keyboard()
        #     )

        state["_prompt"] = "📤 请发送要投稿的帖子区名称，例如：灌水"

    @send_thread.got(
        "channel_name", MessageTemplate("{_prompt}"), [channel_handle_cancel]
    )
    async def got_target_channel(
        bot: Bot,
        state: T_State,
        event: MessageCreateEvent,
        channel_name: str = ArgPlainText(),
    ):
        sendable_channels: dict[str, str] = state["sendable_channels"]
        try:
            state["target_channel_id"] = sendable_channels[channel_name]
        except Exception as ex:
            logger.warning(ex)
            await send_thread.reject(
                f"❌ 帖子版块：{channel_name} 不存在，请重新输入正确的帖子版块名"
            )
        state["target_channel_name"] = channel_name
        state["source_channel_id"] = event.channel_id
        state["source_channel_name"] = await get_channel_name(bot=bot, event=event)
        state["author"] = event.author

    @send_thread.handle()
    async def do_send(bot: Bot, state: T_State, event: MessageCreateEvent):
        upload = do_parse(state)
        md_content = await upload.generate()
        request_id = database.get_request_id()
        try:
            logger.info(f"标题：{upload.title}，投稿内容：{md_content}")
            await bot.put_thread(
                channel_id=upload.info.target_channel.id,
                title=f"[{str(request_id).zfill(3)}]{upload.title}",
                content=markdown_to_html(md_content),
                format=2,  # HTML 格式，可更自由地换行
            )

            # record_thread_content 必须在 record_thread_id 之前执行
            async with record_lock:
                logger.info("开始记录帖子内容")
                database.record_thread_content(
                    user_id=upload.author.id,
                    channel_id=int(upload.info.source_channel.id),
                    request_id=request_id,
                    text=f"{md_content[:300]}..."
                    if len(md_content) > 300
                    else md_content,
                )
        except ActionFailed as af:
            logger.warning(f"发帖失败：{af}")
            if af.code == 11264:
                await send_thread.finish(
                    "🆖 无权限发帖，请在 机器人-权限设置中启用【子频道帖子发布】"
                )
            else:
                await send_thread.finish(
                    af.message if af.message else "🆖 帖子发送失败，请联系bot管理员"
                )
        except Exception as ex:
            logger.warning(f"发帖失败：{ex}")
            await send_thread.send("🆖 帖子发送失败，请联系bot管理员")
        else:
            await send_thread.send(
                MessageSegment.text("🆗 帖子成功发送至")
                + MessageSegment.mention_channel(upload.info.target_channel.id)
            )


async def record_thread_id(event: ForumThreadUpdateEvent):
    """记录帖子id，关联用户和帖子"""
    # 防止thread_id提前于thread_content记录导致关联失败
    async with record_lock:
        pass
    logger.info("收到bot的帖子事件。开始关联用户与帖子")
    thread_id: str = [
        per_info[1] for per_info in event.thread_info if per_info[0] == "thread_id"
    ][0]
    raw_thread_title: RichText = [
        per_info[1] for per_info in event.thread_info if per_info[0] == "title"
    ][0]
    title = raw_thread_title.paragraphs[0].elems[0].text.text
    database.add_thread(channel_id=event.channel_id, thread_id=thread_id, title=title)
