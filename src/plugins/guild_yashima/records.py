"""
消息存储、词云等
有参考 https://github.com/he0119/nonebot-plugin-wordcloud
"""
import asyncio
import concurrent.futures
import datetime
import json
import re
from datetime import timedelta
from functools import partial, reduce
from io import BytesIO
from typing import Dict

import jieba
import jieba.analyse
import jsonpath_ng as jsonpath
from emoji import replace_emoji
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import EventMessage, CommandArg
from nonebot_plugin_apscheduler import scheduler
from wordcloud import WordCloud

from .db import *
from .utils import *


async def save_guild_img_url_handle(event: GuildMessageEvent, message: Message = EventMessage()):
    """
    保存所有频道的图片url
    """
    if message.count("image") == 0:
        return

    segment = message["image", 0]
    match = re.search(r"url=([^]]+)", str(segment))
    if match:
        url = match.group(1)
        model = GuildImgRecord(
            channel_id=event.channel_id, user_id=event.get_user_id(), content=url
        )
        model.save()
    else:
        logger.warning("无法找到url")


async def save_recv_guild_msg_handle(event: GuildMessageEvent):
    """
    保存所有频道文本消息
    """
    msg = event.get_plaintext()

    if len(msg) > 1000 or msg == "":
        return
    model = GuildMessageRecord(
        channel_id=event.channel_id, user_id=event.get_user_id(), content=msg
    )
    model.save()


@scheduler.scheduled_job("interval", minutes=30, id="clear_overtime_message_record")
async def clear_overtime_message_record():
    msg_save_days = int(get_config()["db"]["msg_save_days"])
    msg_query = GuildMessageRecord.delete().where(
        GuildMessageRecord.recv_time < (
            datetime.now() - timedelta(days=msg_save_days))
    )
    img_query = GuildImgRecord.delete().where(
        GuildImgRecord.recv_time < (
            datetime.now() - timedelta(days=msg_save_days))
    )
    msg_num = msg_query.execute()
    img_num = img_query.execute()
    if msg_num > 0 or img_query > 0:
        logger.info(f"已删除频道聊天记录{msg_num}条，聊天图片{img_num}条")


async def resend_pc_unreadable_msg_handle(matcher: Matcher, _: GuildMessageEvent, message: Message = EventMessage()):
    """
    解析PC不可读消息并转换发送
    """
    if message.count("json") == 0:
        return

    segment = message["json", 0]
    json_data = json.loads(segment.get("data").get("data"))

    def get_json(path: str):
        try:
            return jsonpath.parse(path).find(json_data)[0].value
        except IndexError:
            return None

    app = get_json("$.app")
    link, title = None, None

    if app == "com.tencent.channel.share":
        link = get_json("$.meta.detail.link")
        title = get_json("$.meta.detail.title")
    elif app == "com.tencent.miniapp_01":
        link = get_json("$.meta.detail_1.qqdocurl")
        title = get_json("$.meta.detail_1.desc")
    elif app == "com.tencent.structmsg":
        view = get_json("$.view")
        link = get_json(f"$.meta.{view}.jumpUrl")
        title = get_json(f"$.meta.{view}.title")

    if not link or len(link) > 300 or not link.startswith("http"):
        return
    if len(title) > 50:
        title = title[:50] + "…"
    elif not title:
        title = "エラー：タイトルを解析することができません"

    # 处理url防止qq二度解析（在http后添加一个零宽空格）
    # link = link.replace("http", "http\u200b")
    if link.count("www.bilibili.com") != 0:
        link = link.replace("www.bilibili.com", "(被藤子屏蔽，请手动修改为b站域名)")
    if link.count("https", 0, 7) != 0:
        link = link.replace("https://", "")
    elif link.count("http", 0, 7) != 0:
        link = link.replace("http://", "")

    to_send = f"🔗 こちらはURLです：\n{title}\n{link}\nフンス、藤こより、私の方が高性能でしょう！😤"
    await matcher.send(to_send)


async def resend_system_recalled_img_handle(matcher: Matcher, event: GuildMessageEvent, message: Message = EventMessage()):
    """
    发送用户在该频道的最后一次发送的图片的url
    """
    query = (GuildImgRecord
             .select()
             .where((GuildImgRecord.channel_id == event.channel_id) & (GuildImgRecord.user_id == event.get_user_id()))
             .order_by(GuildImgRecord.recv_time.desc())
             .first())

    if query:
        to_send = f"🔗 こちらはURLです：\n{query.content}\nフンだ、なんて高性能でしょうわたしは！😤"
        await matcher.send(to_send)
    else:
        await matcher.send("検索中、検索中......🔍。データが見つかりません")


async def yesterday_wordcloud_handle(matcher: Matcher, event: GuildMessageEvent, args: Message = CommandArg()):
    yesterday = datetime.now() - timedelta(days=1)
    start_time = yesterday.replace(hour=0, minute=10, second=0, microsecond=0)
    end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    channel_id = args.extract_plain_text()
    await matcher.send("ワードクラウドをジェネレートしますね。検索中、検索中......🔍")

    resp = "指定されたチャンネル"
    if not channel_id:
        channel_id = event.channel_id
        resp = "このチャンネル"
    else:
        channel_id = int(channel_id)
    image = await get_wordcloud_by_time(channel_id, start_time, end_time)
    if image:
        await matcher.send(
            f"ふっふっふ、{resp}のワードクラウドがジェネレートしました🎉、さすが高性能なわたし！😊"
            + MessageSegment.image(image)
        )
    else:
        await matcher.send(
            at_user(event) + f"{resp}のチャットレコードが足りないようです"
        )


@scheduler.scheduled_job("cron", minute="10", hour="0", id="yesterday_wordcloud_job")
async def yesterday_wordcloud_job():
    try:
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(
            hour=0, minute=10, second=0, microsecond=0)
        end_time = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=0)
        channels = query_wordcloud_generatable_channel_ids(
            start_time, end_time)
        logger.info(f"以下频道将生成词云：{channels}")
        for channel in channels:
            logger.info(f"开始生成词云，频道ID:{channel}")

            notice = "えっと、そろそろワードクラウドの時間です。検索中、検索中......🔍"
            await get_bot().send_guild_channel_msg(
                guild_id=get_active_guild_id(), channel_id=channel, message=notice
            )

            image = await get_wordcloud_by_time(channel, start_time, end_time)
            if image:
                msg = "ふっふっふ、このチャンネルのワードクラウドがジェネレートしました🎉、さすが高性能なわたし！😊" + \
                    MessageSegment.image(image)
                await get_bot().send_guild_channel_msg(
                    guild_id=get_active_guild_id(), channel_id=channel, message=msg
                )
            else:
                msg = "すいません、チャットレコードが足りないようです"
                await get_bot().send_guild_channel_msg(
                    guild_id=get_active_guild_id(), channel_id=channel, message=msg
                )

        logger.info(f"开始生成全频道词云")
        image = await get_wordcloud_by_time(0, start_time, end_time)
        if image:
            msg = "おまけに💎ヤシマ作戦指揮部💎のフルワードクラウドがジェネレートしました🎉、これこそわたしが高性能である証です！✌️" + \
                MessageSegment.image(image)
            await get_bot().send_guild_channel_msg(
                guild_id=get_active_guild_id(),
                channel_id=get_config()["wordcloud"]["overall_target_channel"],
                message=msg,
            )
        else:
            logger.error("全频道词云图片未生成")
    except Exception as ex:
        # 有点哈人，姑且先发送到测试频
        # 得把发送失败后的逻辑改成失败即重试数次
        # 通常都是签名服务器错误造成的，notice很大可能也发不出去
        notice = "メモリーがロストのようです😦、申し訳ございません"
        await get_bot().send_guild_channel_msg(
            guild_id=get_active_guild_id(), channel_id=get_config()["debug"]["test_channel"], message=notice
        )
        logger.error(f"生成词云异常：{ex}")


def query_wordcloud_generatable_channel_ids(start_time: datetime, end_time: datetime) -> List[int]:
    """
    查找符合生成词云条件的所有子频道
    """
    threshold = get_config()["wordcloud"]["generation_threshold"]
    query = (
        GuildMessageRecord.select(GuildMessageRecord.channel_id, fn.COUNT(
            GuildMessageRecord.channel_id).alias("cnt"))
        .where((GuildMessageRecord.recv_time > start_time)
               & (GuildMessageRecord.recv_time < end_time))
        .group_by(GuildMessageRecord.channel_id)
        .having(fn.COUNT(GuildMessageRecord.channel_id) > threshold)  # 第一次阈值检查
    )
    pre_lst = [model.channel_id for model in query]
    return [check_guild_messages(i, start_time, end_time) for i in pre_lst if check_guild_messages(i, start_time, end_time) is not None]


def check_guild_messages(channel_id: int, start_time: datetime, end_time: datetime) -> int:
    """
    第二次阈值检查，确保在加载了用户黑名单后消息数量仍能达到阈值
    """
    import operator

    expressions = [
        (GuildMessageRecord.recv_time > start_time),
        (GuildMessageRecord.recv_time < end_time),
    ]
    expressions.append(GuildMessageRecord.channel_id == channel_id)
    blacklist = get_config()["wordcloud"]["blacklist_user_ids"]
    if blacklist:
        expressions.append(GuildMessageRecord.user_id.not_in(blacklist))
    query = GuildMessageRecord.select().where(reduce(operator.and_, expressions))
    messages = [model.content for model in query]
    threshold = get_config()["wordcloud"]["generation_threshold"]
    disabled_channels = get_config()["wordcloud"]["disabled_channels"]
    if len(messages) < threshold:
        return None
    for disabled_channel in disabled_channels:
        if channel_id == disabled_channel:
            return None
    return channel_id


async def get_wordcloud_by_time(
    channel_id: int, start_time: datetime, end_time: datetime
) -> Optional[BytesIO]:
    """
    channel_id等于0时，查找所有黑名单以外的子频道记录
    """
    import operator

    expressions = [
        (GuildMessageRecord.recv_time > start_time),
        (GuildMessageRecord.recv_time < end_time),
    ]
    if channel_id != 0:
        expressions.append(GuildMessageRecord.channel_id == channel_id)
    else:
        blacklist_channels = get_config()["wordcloud"]["blacklist_channels"]
        expressions.append(
            GuildMessageRecord.channel_id.not_in(blacklist_channels))
    blacklist = get_config()["wordcloud"]["blacklist_user_ids"]
    if blacklist:
        expressions.append(GuildMessageRecord.user_id.not_in(blacklist))

    query = GuildMessageRecord.select().where(reduce(operator.and_, expressions))
    messages = [model.content for model in query]
    anti_repeat_channels = get_config()["wordcloud"]["anti_repeat_channels"]

    # 针对老干部读报间处理，目前不是很优雅，未来可能会修改
    if anti_repeat_channels and channel_id == 0:
        special_expressions = [
            (GuildMessageRecord.recv_time > start_time),
            (GuildMessageRecord.recv_time < end_time),
        ]
        if blacklist:
            special_expressions.append(
                GuildMessageRecord.user_id.not_in(blacklist))
        special_expressions.append(
            GuildMessageRecord.channel_id == anti_repeat_channels)
        query = GuildMessageRecord.select().where(
            reduce(operator.and_, special_expressions))
        pre_anti_repeat_messages = [model.content for model in query]
        anti_repeat_messages = []
        for anti_repeat_msg in pre_anti_repeat_messages:
            anti_repeat_msg = pre_process(anti_repeat_msg)
            anti_repeat_msg = anti_repeat_process(anti_repeat_msg)
            anti_repeat_messages.append(anti_repeat_msg)
        messages = anti_repeat_messages + messages

    return await get_wordcloud_img(messages)


def anti_repeat_process(msg: str):
    """
    使用jiebafen分词来去除同一条消息内的大量重复词语
    """
    words = jieba.analyse.extract_tags(msg)
    message = " ".join(words)
    return message


def pre_process(msg: str) -> str:
    """对消息进行预处理"""
    # 去除网址
    # https://stackoverflow.com/a/17773849/9212748
    msg = re.sub(
        r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})",
        "",
        msg,
    )
    # 去除 \u200b
    msg = re.sub(r"\u200b", "", msg)
    # 去除 emoji
    # https://github.com/carpedm20/emoji
    msg = replace_emoji(msg)
    return msg


def analyse_message(msg: str) -> Dict[str, float]:
    """
    分析消息
    分词，并统计词频
    """
    # 设置停用词表
    if get_config()["wordcloud"]["stopwords_path"]:
        jieba.analyse.set_stop_words(
            get_config()["wordcloud"]["stopwords_path"])
    # 加载用户词典
    # if plugin_config.wordcloud_userdict_path:
    #     jieba.load_userdict(str(plugin_config.wordcloud_userdict_path))
    # 基于 TF-IDF 算法的关键词抽取
    # 返回所有关键词，因为设置了数量其实也只是 tags[:topK]，不如交给词云库处理
    words = jieba.analyse.extract_tags(msg, topK=0, withWeight=True)
    return {word: weight for word, weight in words}


def _get_wordcloud_img(messages: List[str]) -> Optional[BytesIO]:
    message = " ".join(messages)
    # 预处理
    message = pre_process(message)
    # 分析消息。分词，并统计词频
    frequency = analyse_message(message)
    # 词云参数
    wordcloud_options = {}
    wordcloud_options.update(get_config()["wordcloud"]["options"])
    wordcloud_options.setdefault(
        "font_path", str(get_config()["wordcloud"]["font_path"])
    )
    wordcloud_options.setdefault("width", get_config()["wordcloud"]["width"])
    wordcloud_options.setdefault("height", get_config()["wordcloud"]["height"])
    wordcloud_options.setdefault(
        "background_color", get_config()["wordcloud"]["background_color"]
    )
    wordcloud_options.setdefault("colormap", get_config()[
                                 "wordcloud"]["colormap"])
    try:
        wordcloud = WordCloud(**wordcloud_options)
        image = wordcloud.generate_from_frequencies(frequency).to_image()
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        return image_bytes
    except ValueError:
        pass


async def get_wordcloud_img(messages: List[str]) -> Optional[BytesIO]:
    loop = asyncio.get_running_loop()
    pfunc = partial(_get_wordcloud_img, messages)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, pfunc)
