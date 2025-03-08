from typing import Union

import nonebot
from nonebot import on_command, on_notice, on_message
from nonebot.log import logger
from nonebot.rule import to_me, is_type
from nonebot.matcher import Matcher
from nonebot.adapters import MessageTemplate, Message
from nonebot.params import ArgPlainText, CommandArg
from nonebot.adapters.qq import (
    Bot,
    MessageCreateEvent,
    MessageSegment,
    ForumPostCreateEvent,
    ForumReplyCreateEvent,
    ForumThreadUpdateEvent,
    ActionFailed,
)
from nonebot.adapters.qq.models import RichText
from nonebot.typing import T_State

from .utils import (
    gen_handle_cancel,
    get_event_img,
    get_user_nick,
    get_channel_name,
    get_img_size,
    generate_thread_title,
    markdown_to_html,
    replace_qq_emoji,
    get_thread_channels,
    is_bot_thread,
)
from .db_operater import database, UserNotFoundError
from ..utils import get_config


# 指令用法：/一键发帖 <帖子区名称> <投稿内容> <是否提醒帖子评论 默认："是">
forum_send_matcher = on_command("一键发帖", rule=to_me(), priority=1, block=True)
forum_event_matcher = on_notice(
    rule=is_type(Union[ForumPostCreateEvent, ForumReplyCreateEvent])
)
message_event_matcher = on_message(rule=is_type(MessageCreateEvent))
forum_record_matcher = on_notice(rule=is_type(ForumThreadUpdateEvent) & is_bot_thread)
forum_help_matcher = on_command("帮助", rule=to_me())
forum_delete_matcher = on_command("撤回发帖", rule=to_me())
database_clear_matcher = on_command("清空帖子数据库", rule=to_me())

channel_handle_cancel = gen_handle_cancel(forum_send_matcher, "🆗 已取消")

config = nonebot.get_driver().config
TIMEOUT_MINUTE: str = f"{(config.session_expire_timeout.seconds % 3600) // 60}分钟"
CANCEL_PROMPT: str = "⛔ 中止操作请输入'取消'"
DEFAULT_CHANNEL_NAME: str | None = get_config()["forum"]["default_channel_name"]
DEFAULT_NEED_NOTICE: bool = True


@message_event_matcher.handle()
async def receive_msg(event: MessageCreateEvent):
    if user := event.author:
        logger.info(f"消息用户ID：{user.id}")
    if msg_reply := event.reply:
        logger.warning("发现回复")
        if msg_reply.author:
            logger.warning(f"回复者ID：{msg_reply.author.id}")
        if msg_reply.content:
            logger.warning(f"回复内容：{msg_reply.content}")
        if msg_reply.attachments:
            for per_attach in msg_reply.attachments:
                logger.warning(f"回复图片：{per_attach.url}")


@forum_event_matcher.handle()
async def receive_forum(
    bot: Bot, event: Union[ForumPostCreateEvent, ForumReplyCreateEvent]
):
    logger.warning(f"收到帖子EVENT：{type(event)}")
    logger.warning(f"用户id：{event.author_id}")
    nick_name = "未知昵称"
    try:
        nick_name = (
            await bot.get_member(guild_id=event.guild_id, user_id=event.author_id)
        ).nick
    except ActionFailed as af:
        logger.warning(f"无法获取昵称：{af}，用户id：{event.author_id}")
    logger.warning(f"用户昵称：{nick_name}")


@database_clear_matcher.handle()
async def are_you_sure(_: MessageCreateEvent, state: T_State):
    state["_prompt"] = (
        "◤◢◤◢◤◢◤◢◤◢◤◢\n即将清空所有的帖子记录！！\n◤◢◤◢◤◢◤◢◤◢◤◢\n📝 请输入'I AM CERTAIN WHAT IM DOING'确认清空 | 其他内容则清空取消"
    )


@database_clear_matcher.got("confirm", MessageTemplate("{_prompt}"))
async def clear_forum_database(_: MessageCreateEvent, confirm: str = ArgPlainText()):
    if confirm == "I AM CERTAIN WHAT IM DOING":
        logger.info("开始清空数据库")
        database.clear_db()
    else:
        await database_clear_matcher.finish("🆗 已取消")


@forum_record_matcher.handle()
async def record_thread(event: ForumThreadUpdateEvent):
    thread_id: str = [
        per_info[1] for per_info in event.thread_info if per_info[0] == "thread_id"
    ][0]
    raw_thread_title: RichText = [
        per_info[1] for per_info in event.thread_info if per_info[0] == "title"
    ][0]
    title = raw_thread_title.paragraphs[0].elems[0].text.text
    database.add_thread(channel_id=event.channel_id, thread_id=thread_id, title=title)


@forum_delete_matcher.handle()
async def prepare_confirm(event: MessageCreateEvent, state: T_State):
    try:
        thread = database.get_last_thread(event.get_user_id())
    except UserNotFoundError:
        await forum_delete_matcher.finish(
            "❌ 帖子记录不存在，仅可撤回自己使用'/一键发帖'发送的帖子"
        )
    except Exception as ex:
        logger.warning(ex)
        await forum_delete_matcher.finish("🆖 出错了，请联系bot管理员")
    else:
        state["thread_channel_id"] = str(thread.thread_channel_id)
        state["thread_id"] = thread.thread_id
        state["_prompt"] = (
            f"🚨 即将撤回帖子【{thread.title}】\n✨ 如果需要撤回更早的帖子，请联系管理手动处理\n📝 输入'确认'确认撤回 | 其他内容取消撤回"
        )


@forum_delete_matcher.got("confirm", MessageTemplate("{_prompt}"))
async def got_confirm(
    bot: Bot, event: MessageCreateEvent, state: T_State, confirm: str = ArgPlainText()
):
    if confirm == "确认":
        try:
            database.del_last_thread(event.get_user_id())
            await bot.delete_thread(
                channel_id=state["thread_channel_id"], thread_id=state["thread_id"]
            )
        except Exception as ex:
            logger.warning(ex)
            await forum_event_matcher.finish("🆖 出错了，请联系bot管理员")
        else:
            await forum_event_matcher.finish("🆗 成功撤回")
    else:
        forum_delete_matcher.finish("🆗 已取消")


@forum_help_matcher.handle()
async def send_help(matcher: Matcher, _: MessageCreateEvent):
    prompt = f"""✨ /一键发帖

🛠️ 基础用法：
    直接输入 '@bot /一键发帖 <帖子区完整名称> <投稿内容>'

📃 参数说明：
    帖子区完整名称：可选，默认为 {DEFAULT_CHANNEL_NAME}（若帖子区中不存在{DEFAULT_CHANNEL_NAME}区则必须指定）
    投稿内容：必须，类型可为 文字 或 图文 或 图片。支持 Markdown* 部分格式
    ※ 参数之间需用空格间隔
    ※ Markdown 支持详情：\nhttps://bot.q.qq.com/wiki/develop/api/openapi/message/format/markdown/markdown.html

🛠️ 特殊用法：
    - 长按引用想要投稿的消息
    - 删除@被引用人（如果有的话）
    - 保持引用消息状态并输入 '@bot /一键发帖 <帖子区完整名称>'

📃 参数说明：
    帖子区完整名称：可选，默认为 {DEFAULT_CHANNEL_NAME}（若帖子区中不存在{DEFAULT_CHANNEL_NAME}区则必须指定）
"""
    await matcher.finish(prompt)


@forum_send_matcher.handle()
async def prepare_get_channel_name(
    matcher: Matcher,
    bot: Bot,
    event: MessageCreateEvent,
    state: T_State,
    raw_args: Message = CommandArg(),
):
    if not DEFAULT_CHANNEL_NAME:
        forum_send_matcher.finish("🆖 机器人配置错误，请联系机器人管理员")
        raise Exception("默认帖子区未配置，请检查配置文件")
    # 获取可发送的帖子区
    sendable_channels: dict[str, str] = await get_thread_channels(bot, event)
    # 检查回复内容
    # state["source_channel_id"] = event.channel_id
    if msg_reply := event.reply:
        state["has_reply"] = True
        # state["source_user_id"] = msg_reply.author.id
        if msg_reply.author.id == event.author.id:
            state["reply_myself"] = True
        else:
            state["reply_myself"] = False
        # 跳过询问
        matcher.set_arg("raw_text", raw_args)
        state["upload_content"] = (
            replace_qq_emoji(msg_reply.content) if msg_reply.content else None
        )
        state["image_urls"] = (
            [per_attach.url for per_attach in msg_reply.attachments]
            if msg_reply.attachments
            else None
        )
    else:
        state["has_reply"] = False
        # state["source_user_id"] = event.author.id
    # 检查参数
    if arg_text := raw_args.extract_plain_text():
        args = arg_text.split(" ")
        # （未实现）<是否提醒>
        if args[-1] in ["是", "提醒", "开启", "开"]:
            state["notice"] = True
        elif args[-1] in ["否", "不提醒", "不", "关闭", "关"]:
            state["notice"] = False
        else:
            state["notice"] = DEFAULT_NEED_NOTICE
        # <帖子区名称>
        if args[0] in sendable_channels.keys():
            state["target_channel_name"] = args[0]
            state["target_channel_id"] = sendable_channels[args[0]]
        else:
            state["target_channel_id"] = None
            state["target_channel_name"] = None
        # 跳过询问
        matcher.set_arg("raw_text", raw_args)
    else:
        state["notice"] = DEFAULT_NEED_NOTICE
        state["target_channel_name"] = None
        state["target_channel_id"] = None

    if img_urls := get_event_img(event):
        state["image_urls"] = img_urls
        # 跳过询问
        matcher.set_arg("raw_text", raw_args)
    elif not state["has_reply"]:
        state["image_urls"] = None
    res_text = "📝 请输入投稿内容，可附带图片\n"
    res_text += f"⏱️ {TIMEOUT_MINUTE}内有效\n{CANCEL_PROMPT}"

    state["_prompt"] = res_text
    state["sendable_channels"] = sendable_channels


@forum_send_matcher.got(
    "raw_text", MessageTemplate("{_prompt}"), [channel_handle_cancel]
)
async def got_upload_content(
    matcher: Matcher,
    event: MessageCreateEvent,
    state: T_State,
    _: MessageCreateEvent,
    raw_text: str = ArgPlainText(),
):
    if raw_text == "帮助":
        arg_info = f"<（可选）帖子区完整名称 默认：{DEFAULT_CHANNEL_NAME}>\n<（{'可选' if state['has_reply'] else '必须'}）投稿内容，可附带图片>"
        await matcher.reject(
            f"📃 指令的参数：\n{arg_info}\n📝 参数之间需用空格间隔\n🚨 投稿内容中包含过长的数字会被吞，如果有需要请使用大写数字（壹贰叁）\n"
            + f"⏱️ 请输入参数，{TIMEOUT_MINUTE}内有效\n"
            + f"{CANCEL_PROMPT}"
        )

    # 删除投稿内容中的多余参数
    upload_content = raw_text.split(" ")
    sendable_channels: dict[str, str] = state["sendable_channels"]
    if state["target_channel_id"] is not None:  # 帖子区参数在一开始已经传入
        upload_content.pop(0)
    elif upload_content[0] in sendable_channels.keys():  # 帖子区参数在询问后传入
        state["target_channel_name"] = upload_content[0]
        state["target_channel_id"] = sendable_channels[upload_content[0]]
        upload_content.pop(0)
    else:  # 帖子区参数在询问后未传入
        try:
            state["target_channel_name"] = DEFAULT_CHANNEL_NAME
            state["target_channel_id"] = sendable_channels[DEFAULT_CHANNEL_NAME]
        except KeyError:
            logger.warning(f"帖子区：{DEFAULT_CHANNEL_NAME}不存在")
            await matcher.reject(
                f"❌ 默认帖子区 #{DEFAULT_CHANNEL_NAME} 不存在，请手动指定帖子区\n❓ 输入'帮助'查看帮助"
            )
    # 提醒相关功能待实现
    # if not state["notice"]:
    #   upload_content.pop()
    #   source_channel_id = state["source_channel_id"]
    #   source_user_id = state["source_user_id"]

    # 拼接回复文本和源文本
    # 有回复
    if state["has_reply"]:
        source_text = f"{state['upload_content']}" if state["upload_content"] else ""
        # 发送了参数
        if upload_content:
            reply_text = (
                " ".join(upload_content) + "\n\n" if upload_content[0] else ""
            )  # 此时 upload_content 中应只有一个元素
            reply_text += "转发消息：\n"
        # 无参数
        else:
            reply_text = "转发消息：\n"
        state["upload_content"] = reply_text + source_text
        state["title"] = generate_thread_title(
            reply_text if upload_content else source_text
        )
    # 没有回复
    else:
        state["upload_content"] = " ".join(upload_content)
        state["image_urls"] = get_event_img(event) if get_event_img(event) else None
        # 有参数
        if upload_content:
            state["title"] = generate_thread_title(
                upload_content[0] if upload_content[0] else "分享图片"
            )
        # 无参数
        else:
            state["title"] = "分享图片"


@forum_send_matcher.handle()
async def send_thread(bot: Bot, state: T_State, event: MessageCreateEvent):
    # 添加来源（子频道，用户名）
    md_content = f"🔃 转发自 #{await get_channel_name(bot, event)}\n"
    if state["has_reply"]:
        md_content += (
            f"🆔 {await get_user_nick(bot, event)}\n" if state["reply_myself"] else ""
        )
    else:
        md_content += f"🆔 {await get_user_nick(bot, event)}\n"
    md_content += "![分隔符 #1320 #130](https://i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png@progressive.webp)\n"
    # 添加文字与图片
    if state["upload_content"]:
        raw_text: str = state["upload_content"]
        md_content += raw_text + "\n"
    if img_urls := state["image_urls"]:
        for per_url in img_urls:
            img_w, img_h = await get_img_size(per_url)
            md_content += f"![图片 #{img_w}px #{img_h}px]({per_url})\n"

    request_id = database.get_request_id()
    try:
        logger.info(f"标题：{state['title']}，投稿内容：{md_content}")
        await bot.put_thread(
            channel_id=state["target_channel_id"],
            title=f"[{str(request_id).zfill(3)}]{state['title']}",
            content=markdown_to_html(md_content),
            format=2,  # HTML 格式，可更自由地换行
        )
    except Exception as ex:
        logger.warning(f"发帖失败：{ex}")
        await forum_send_matcher.send("🆖 帖子发送失败，请联系bot管理员")
    else:
        await forum_send_matcher.send(
            MessageSegment.text("🆗 帖子成功发送至")
            + MessageSegment.mention_channel(state["target_channel_id"])
        )
    database.record_thread_content(
        user_id=event.get_user_id(),
        channel_id=int(event.channel_id),
        request_id=request_id,
        text=f"{md_content[:300]}..." if len(md_content) > 300 else md_content,
    )
    await forum_send_matcher.finish()
