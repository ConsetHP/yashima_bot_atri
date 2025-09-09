"""
分析消息并选择主题渲染词云
"""

import re
import asyncio
import concurrent.futures
from io import BytesIO
from typing import Optional
from functools import partial

import jieba
import jieba.analyse
from nonebot.log import logger
from emoji import replace_emoji

from .theme import theme_manager
from ..utils import get_config


def anti_repeat_process(msg: str) -> str:
    """使用jieba分词来去除同一条消息内的大量重复词语"""
    words: list[str] = jieba.analyse.extract_tags(msg)
    # 去除长度小于3的数字
    processed_words = [
        "" if word.isdigit() and len(word) < 3 else word for word in words
    ]
    message = " ".join(processed_words)
    return message


def pre_process(msg: str) -> str:
    """对消息进行预处理"""
    # 去除常见机器人指令
    msg = remove_bot_command_prefix(msg)
    # 去除使用了b站复制链接功能产生的消息
    msg = re.sub(r"^【.+?-哔哩哔哩】 https://b23\.tv/\w+$", "", msg)
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


def remove_bot_command_prefix(msg: str) -> str:
    """删除以bot指令为开头的消息，例：/打卡"""
    if blacklist_bot_commands := get_config()["wordcloud"]["blacklist_bot_commands"]:
        for per_cmd in blacklist_bot_commands:
            msg = "" if msg.startswith(per_cmd) else msg
        return msg
    else:
        return msg


def analyse_message(msg: str) -> dict[str, float]:
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


async def get_wordcloud_img(messages: list[str]) -> Optional[BytesIO]:
    """分析消息并渲染词云图片"""
    # 全部都用jieba提前分词，可以让最终输入词云库的权重更合理
    jieba_messages = [pre_process(msg) for msg in messages]
    message = " ".join(jieba_messages)
    # 分析消息。分词，并统计词频
    frequency = analyse_message(message)

    if not get_config()["wordcloud"]["theme"]:
        logger.warning("未设置主题，无法渲染词云")
        return
    else:
        theme_name = get_config()["wordcloud"]["theme"]
    if theme := theme_manager[theme_name]:
        logger.info(f"Try to render wordcloud with theme {theme_name}")
        loop = asyncio.get_running_loop()
        pfunc = partial(theme.do_render, frequency)
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, pfunc)
