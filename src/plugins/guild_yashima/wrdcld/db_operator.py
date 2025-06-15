"""
数据库操作相关
"""

from datetime import datetime
from functools import reduce
from typing import List, Optional

from peewee import fn

from ..diary.db_model import QQGuildMessageRecord as GuildMessageRecord
from ..utils import get_config


def query_wordcloud_generatable_channel_ids(
    start_time: datetime, end_time: datetime
) -> List[int]:
    """查找符合生成词云条件的所有子频道"""
    threshold = get_config()["wordcloud"]["generation_threshold"]
    blacklist_users = get_config()["wordcloud"]["blacklist_user_ids"]
    query = (
        GuildMessageRecord.select(
            GuildMessageRecord.channel_id,
            fn.COUNT(GuildMessageRecord.channel_id).alias("cnt"),
        )
        .where(
            (GuildMessageRecord.recv_time > start_time)
            & (GuildMessageRecord.recv_time < end_time)
            & (GuildMessageRecord.user_id.not_in(blacklist_users))
        )  # 排除黑名单用户
        .group_by(GuildMessageRecord.channel_id)
        .having(fn.COUNT(GuildMessageRecord.channel_id) > threshold)  # 阈值检查
    )
    channels = [model.channel_id for model in query]
    return channels


async def get_wordcloud_by_time(
    channel_id: int, start_time: datetime, end_time: datetime
) -> Optional[list[str]]:
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
        expressions.append(GuildMessageRecord.channel_id.not_in(blacklist_channels))
    if blacklist_users := get_config()["wordcloud"]["blacklist_user_ids"]:
        expressions.append(GuildMessageRecord.user_id.not_in(blacklist_users))

    query = GuildMessageRecord.select().where(reduce(operator.and_, expressions))
    return [model.content for model in query]
