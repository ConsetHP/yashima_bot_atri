"""
消息存储、词云等
有参考 https://github.com/he0119/nonebot-plugin-wordcloud
TO DO: 将 アトリ 的高性能消息抽象成一个类，方便增加和修改
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
from pathlib import Path

import jieba
import jieba.analyse
import jsonpath_ng as jsonpath
import numpy as np
from PIL import Image
from emoji import replace_emoji
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import EventMessage, CommandArg
from nonebot_plugin_apscheduler import scheduler
from wordcloud import WordCloud
from wordcloud import ImageColorGenerator

from .db import *
from .utils import *
from .send import send_msgs
from .character import *


async def save_guild_img_url_handle(event: GuildMessageEvent, message: Message = EventMessage()):
    """保存所有频道的图片url"""
    if message.count("image") == 0:
        return

    try:
        for msg in event.get_message():
            if msg.type in ["image", "attachment"]:
                url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
                model = GuildImgRecord(
                channel_id=event.channel_id, user_id=event.get_user_id(), content=url
                )
                model.save()
    except Exception as e:
        logger.warning(f"出现错误：{e}")


async def save_recv_guild_msg_handle(event: GuildMessageEvent):
    """保存所有频道文本消息"""
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
    if msg_num > 0 or img_num > 0:
        logger.info(f"已删除频道聊天记录{msg_num}条，聊天图片{img_num}条")


async def resend_pc_unreadable_msg_handle(_: Matcher, event: GuildMessageEvent, message: Message = EventMessage()):
    """解析PC不可读消息并转换发送"""
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

    if not link or len(link) > 600 or not link.startswith("http"):
        logger.warning(f"链接异常：{link}")
        return
    if len(title) > 50:
        title = title[:50] + "…"
    elif not title:
        title = f"{Atri.general_word("error")}：タイトルを解析することができません"

    # 处理url防止qq二度解析（在http后添加一个零宽空格）
    # link = link.replace("http", "http\u200b")
    if link.count("www.bilibili.com") != 0:
        link = link.replace("www.bilibili.com", "(请手动修改为b站域名)")
    if link.count("https", 0, 7) != 0:
        link = link.replace("https://", "")
    elif link.count("http", 0, 7) != 0:
        link = link.replace("http://", "")

    to_send = f"🔗 こちらはURLです：\n{title}\n{link}\n{Atri.general_word("modal_particle")}、{Atri.general_word("fuck_tencent")}"
    await send_msgs(event.channel_id, to_send)


async def resend_system_recalled_img_handle(_: Matcher, event: GuildMessageEvent):
    """发送用户在该频道的最后一次发送的图片的url"""
    query = (GuildImgRecord
             .select()
             .where((GuildImgRecord.channel_id == event.channel_id) & (GuildImgRecord.user_id == event.get_user_id()))
             .order_by(GuildImgRecord.recv_time.desc())
             .first())

    if query:
        to_send = f"🔗 こちらはURLです：\n{query.content}\n{Atri.general_word("modal_particle")}、{Atri.general_word("proud")}"
        await send_msgs(event.channel_id, to_send)
    else:
        to_send = f"{Atri.general_word("loading")}。データが見つかりません"
        await send_msgs(event.channel_id, to_send)


async def yesterday_wordcloud_handle(_: Matcher, event: GuildMessageEvent, args: Message = CommandArg()):
    yesterday = datetime.now() - timedelta(days=1)
    start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    channel_id = args.extract_plain_text()
    progress_msg = f"ワードクラウドをジェネレートしますね。{Atri.general_word("loading")}"
    await send_msgs(event.channel_id, progress_msg)

    resp = "指定されたチャンネル"
    if not channel_id:
        channel_id = event.channel_id
        resp = "このチャンネル"
    else:
        channel_id = int(channel_id)
    image = await get_wordcloud_by_time(channel_id, start_time, end_time)
    if image:
        msg = MessageSegment.text(f"{Atri.general_word("modal_particle")}、{resp}のワードクラウドがジェネレートしました🎉、{Atri.general_word("proud")}") + MessageSegment.image(image)
        await send_msgs(event.channel_id, msg)
    else:
        msg = at_user(event) + MessageSegment.text(f"{resp}のチャットレコードが足りないようです")
        await send_msgs(event.channel_id, msg)


@scheduler.scheduled_job("cron", minute="10", hour="0", id="yesterday_wordcloud_job")
async def yesterday_wordcloud_job():
    try:
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(
            hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=0)
        channels = query_wordcloud_generatable_channel_ids(
            start_time, end_time)
        if len(channels) > 0:
            logger.info(f"以下频道将生成词云：{channels}")
            for channel in channels:
                # 检查该子频道是否已禁用词云生成
                if channel in get_config()["wordcloud"]["disabled_channels"]:
                    continue

                logger.info(f"开始生成词云，频道ID:{channel}")

                notice = f"{Atri.general_word("discourse_particle")}、そろそろワードクラウドの時間です。{Atri.general_word("loading")}"
                await send_msgs(channel, notice)

                image = await get_wordcloud_by_time(channel, start_time, end_time)
                if image:
                    msg = MessageSegment.text(f"{Atri.general_word("modal_particle")}、このチャンネルのワードクラウドがジェネレートしました🎉、{Atri.general_word("proud")}") + \
                        MessageSegment.image(image)
                    await send_msgs(channel, msg)
                else:
                    logger.error("全频道词云图片未生成")
                    raise Exception("词云图片未生成")
        else:
            notice = f"{Atri.general_word("discourse_particle")}、そろそろワードクラウドの時間です。{Atri.general_word("loading")}"
            await send_msgs(get_config()["wordcloud"]["overall_target_channel"], notice)

        logger.info(f"开始生成全频道词云")
        image = await get_wordcloud_by_time(0, start_time, end_time)
        if image:
            # 极少数情况下，水频不会出子频词云，加个判断去掉 おまけに
            bonus_msg = "おまけに" if len(channels) > 0 else ""
            msg = MessageSegment.text(f"{bonus_msg}💎ヤシマ作戦指揮部💎のフルワードクラウドがジェネレートしました🎉、{Atri.general_word("proud")}") + \
                MessageSegment.image(image)
            await send_msgs(get_config()["wordcloud"]["overall_target_channel"], msg)
        else:
            logger.error("全频道词云图片未生成")
            raise Exception("词云图片未生成")
    except Exception as ex:
        # 通常都是签名服务器错误造成的，notice很大可能也发不出去
        notice = f"{Atri.general_word("error")}"
        await send_msgs(get_config()["debug"]["test_channel"], notice)
        logger.error(f"生成词云异常：{ex}")


def query_wordcloud_generatable_channel_ids(start_time: datetime, end_time: datetime) -> List[int]:
    """查找符合生成词云条件的所有子频道"""
    threshold = get_config()["wordcloud"]["generation_threshold"]
    blacklist_users = get_config()["wordcloud"]["blacklist_user_ids"]
    query = (
        GuildMessageRecord.select(GuildMessageRecord.channel_id, fn.COUNT(
            GuildMessageRecord.channel_id).alias("cnt"))
        .where((GuildMessageRecord.recv_time > start_time)
               & (GuildMessageRecord.recv_time < end_time)
               & (GuildMessageRecord.user_id.not_in(blacklist_users)))  # 排除黑名单用户
        .group_by(GuildMessageRecord.channel_id)
        .having(fn.COUNT(GuildMessageRecord.channel_id) > threshold)  # 阈值检查
    )
    channels = [model.channel_id for model in query]
    return channels


async def get_wordcloud_by_time(
    channel_id: int, start_time: datetime, end_time: datetime
) -> Optional[BytesIO]:
    """channel_id等于0时，查找所有黑名单以外的子频道记录"""
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
    if blacklist_users := get_config()["wordcloud"]["blacklist_user_ids"]:
        expressions.append(GuildMessageRecord.user_id.not_in(blacklist_users))

    query = GuildMessageRecord.select().where(reduce(operator.and_, expressions))
    messages = [model.content for model in query]

    # 全部都用jieba提前分词，可以让最终输入词云库的权重更合理
    jieba_messages = [pre_process(msg) for msg in messages]
    return await get_wordcloud_img(jieba_messages)


def anti_repeat_process(msg: str) -> str:
    """使用jieba分词来去除同一条消息内的大量重复词语"""
    words: list[str] = jieba.analyse.extract_tags(msg)
    # 去除长度小于3的数字
    processed_words = ["" if word.isdigit() and len(word) < 3 else word for word in words]
    message = " ".join(processed_words)
    return message


def pre_process(msg: str) -> str:
    """对消息进行预处理"""
    # 去除常见机器人指令
    msg = remove_bot_command(msg)
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
    # 去除磁力链接
    msg = re.sub(r"magnet:\?[a-zA-Z0-9=&:.%+-]+", "", msg)
    # 防止复读
    msg = anti_repeat_process(msg)
    return msg


def remove_bot_command(msg: str) -> str:
    """删除用户调用bot指令，例：/打卡"""
    if blacklist_bot_commands := get_config()["wordcloud"]["blacklist_bot_commands"]:
        return "" if msg in blacklist_bot_commands else msg
    else:
        return msg


def analyse_message(msg: str) -> Dict[str, float]:
    """
    分析消息
    分词，并统计词频
    """
    # 设置停用词表
    if stopwords_path := get_config()["wordcloud"]["stopwords_path"]:
        jieba.analyse.set_stop_words(stopwords_path)
    # 加载用户词典
    # if plugin_config.wordcloud_userdict_path:
    #     jieba.load_userdict(str(plugin_config.wordcloud_userdict_path))
    # 基于 TF-IDF 算法的关键词抽取
    # 返回所有关键词，因为设置了数量其实也只是 tags[:topK]，不如交给词云库处理
    words = jieba.analyse.extract_tags(msg, topK=0, withWeight=True)
    return {word: weight for word, weight in words}


def _get_wordcloud_img(messages: List[str]) -> Optional[BytesIO]:
    message = " ".join(messages)
    # 分析消息。分词，并统计词频
    frequency = analyse_message(message)
    # 词云参数
    wordcloud_options = {}
    wordcloud_options.update(get_config()["wordcloud"]["options"])
    wordcloud_options.setdefault("width", get_config()["wordcloud"]["width"])
    wordcloud_options.setdefault("height", get_config()["wordcloud"]["height"])
    # 加载主题
    if theme := get_config()["wordcloud"]["theme"]:
        wordcloud_options.setdefault("background_color", None)
        wordcloud_options.setdefault("mode", "RGBA")
        wordcloud_options.setdefault("mask", np.array(Image.open(str(Path(__file__).parent / get_config()["wordcloud"]["mask_path"] / f"{theme}.png"))))
        wordcloud_options.setdefault("font_path", str(Path(__file__).parent / get_config()["wordcloud"]["theme_font_path"] / f"{theme}.otf"))
        wordcloud_options.setdefault("color_func", ImageColorGenerator(np.array(Image.open(str(Path(__file__).parent / get_config()["wordcloud"]["mask_path"] / f"{theme}-color.png")))))
    else:
        wordcloud_options.setdefault(
        "font_path", str(get_config()["wordcloud"]["font_path"])
    )
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
        # 将图片覆盖到主题背景上
        if theme := get_config()["wordcloud"]["theme"]:
            background = Image.open(str(Path(__file__).parent / get_config()["wordcloud"]["background_img_path"] / f"{theme}.png"))
            overlay = Image.open(image_bytes)
            background.paste(overlay, (0, 0), overlay)
            result_bytes = BytesIO()
            background.save(result_bytes, format="PNG")
            return result_bytes
        else:
            return image_bytes
    except ValueError:
        pass


async def get_wordcloud_img(messages: List[str]) -> Optional[BytesIO]:
    loop = asyncio.get_running_loop()
    pfunc = partial(_get_wordcloud_img, messages)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, pfunc)
