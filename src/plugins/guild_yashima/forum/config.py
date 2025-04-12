import nonebot

from ..utils import get_config

config = nonebot.get_driver().config
TIMEOUT_MINUTE: str = f"{(config.session_expire_timeout.seconds % 3600) // 60}分钟"
CANCEL_PROMPT: str = "⛔ 中止操作请输入'取消'"
DEFAULT_CHANNEL_NAME: str | None = get_config()["forum"]["default_channel_name"]
DEFAULT_NEED_NOTICE: bool = True
