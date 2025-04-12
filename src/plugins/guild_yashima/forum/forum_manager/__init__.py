from typing import Union

from nonebot import on_command, on_notice
from nonebot.rule import to_me, is_type
from nonebot.adapters.qq import (
    ForumPostCreateEvent,
    ForumReplyCreateEvent,
    ForumThreadUpdateEvent,
)

from .send_thread import do_send_thread, record_thread_id
from .comment import receive_comment
from .help import send_help
from .delete_thread import do_delete_thread
from .utils import gen_handle_cancel, do_clean_database
from ..utils import is_bot_thread

forum_send_matcher = on_command("一键发帖", rule=to_me())
do_send_thread(forum_send_matcher)
forum_delete_matcher = on_command("撤回发帖", rule=to_me())
do_delete_thread(forum_delete_matcher)

# 未实现
comment_event_matcher = on_notice(
    rule=is_type(Union[ForumPostCreateEvent, ForumReplyCreateEvent]),
    handlers=[receive_comment],
)

forum_record_matcher = on_notice(
    rule=is_type(ForumThreadUpdateEvent) & is_bot_thread, handlers=[record_thread_id]
)
forum_help_matcher = on_command("帮助", rule=to_me(), handlers=[send_help])
database_clean_matcher = on_command("清空帖子数据库", rule=to_me())
do_clean_database(database_clean_matcher)

channel_handle_cancel = gen_handle_cancel(forum_send_matcher, "🆗 已取消")
