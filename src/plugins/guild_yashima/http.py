import re
from re import Match

import httpx
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters import Message

from .utils import get_config


http_headers = {
    "User-Agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82"
}


def http_client(*args, **kwargs):
    if headers := kwargs.get("headers"):
        new_headers = http_headers.copy()
        new_headers.update(headers)
        kwargs["headers"] = new_headers
    else:
        kwargs["headers"] = http_headers
    return httpx.AsyncClient(*args, **kwargs)


def bypass_tencent_url_detection(
    msg: Message[MessageSegment] | MessageSegment | str,
) -> Message:
    """处理消息中的所有URL，防止吞消息"""
    if isinstance(msg, str):
        new_msg = Message(MessageSegment.text(replace_url_dots(msg)))
    elif isinstance(msg, MessageSegment):
        if msg.type == "text":
            new_msg = Message(MessageSegment.text(replace_url_dots(msg.data["text"])))
        else:
            new_msg = Message(msg)
    elif isinstance(msg, Message):
        new_msg = Message()
        for per_msg in msg:
            if per_msg.type == "text":
                processed_msg = MessageSegment.text(
                    replace_url_dots(per_msg.data["text"])
                )
                new_msg.append(processed_msg)
            else:
                new_msg.append(per_msg)
    else:
        logger.warning(f"未知消息类型：{type(msg)}")
        new_msg = msg
    return new_msg


def process_url(url: str) -> str:
    """处理 URL中的参数，减少URL长度"""
    if url.count("mp.weixin.qq.com") != 0:
        # 微信的追踪参数
        base_url, query_string = url.split("?", 1)
        params_to_remove = [
            "chksm",
            "mpshare",
            "scene",
            "srcid",
            "sharer_shareinfo",
            "sharer_shareinfo_first",
        ]
        query_params = query_string.split("&")
        filtered_params = [
            param
            for param in query_params
            if not any(param.startswith(f"{key}=") for key in params_to_remove)
        ]
        url = f"{base_url}?{'&'.join(filtered_params)}"
    elif url.count("www.bilibili.com") != 0 or url.count("b23.tv") != 0:
        # b站的追踪参数
        url = re.sub(r"(\b(?:https?:\/\/|www\.)\S+?)\?[^ \n]*", r"\1", url)
    url_with_prompt = "（PC only）" + url
    return url_with_prompt


def replace_url_dots(text: str) -> str:
    """替换URL中的点"""
    domain_white_list: list[str] = get_config()["general"]["domain_white_list"]
    domain_pattern = re.compile(r"([0-9a-zA-Z-]{1,}\.)+([a-zA-Z]{2,})")
    url_pattern = re.compile(
        r"https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+|www\.[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+"
    )

    # 排除域名白名单
    if match := domain_pattern.search(text):
        domain: str = match.group(0)
        if domain in domain_white_list:
            return text

    def replace_dots(match: Match):
        url: str = match.group(0)
        url = url.replace("https://", "")
        url = url.replace("http://", "")
        url = url.replace("/", "／")
        return url.replace(".", "·")

    return url_pattern.sub(replace_dots, text)
