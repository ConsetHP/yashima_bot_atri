from nonebot.plugin import on_message
from .handler import save_group_message_handle


msg_record = on_message(handlers=[save_group_message_handle])
