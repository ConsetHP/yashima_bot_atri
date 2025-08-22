from typing import Union, Optional
from datetime import datetime
from peewee import fn
from functools import reduce

from nonebot.adapters.qq.models.guild import Member, Channel, Role
from nonebot.log import logger

from .model import (
    GuildMessageRecord,
    ChannelRecord,
    GuildUserRecord,
    GuildRoleRecord,
    UserRoleMapping,
)
from ...database.base import db
from ...utils import get_config


@db.atomic()
def save_guild_message(
    channel: Channel,
    guild_user: Member,
    user_roles: list[Role],
    message_id: str,
    text: Optional[str] = None,
    images: Optional[list[str]] = None,
) -> None:
    """保存频道消息"""
    # 记录子频道信息
    db_channel: Union[ChannelRecord, None] = ChannelRecord.get_or_none(
        (ChannelRecord.channel_id == channel.id)
    )
    if not db_channel:
        # 没有就创建
        db_channel = ChannelRecord.create(
            channel_id=channel.id,
            guild_id=channel.guild_id,
            channel_name=channel.name,
            position=channel.position,
        )
    else:
        # 如果数据库字段与获取的数据不同就更新字段
        if db_channel.channel_name != channel.name:
            db_channel.channel_name = channel.name
            db_channel.save()
        if db_channel.position != channel.position:
            db_channel.position = channel.position
            db_channel.save()

    # 记录用户信息
    db_user: Union[GuildUserRecord, None] = GuildUserRecord.get_or_none(
        (GuildUserRecord.user_id == guild_user.user.id)
    )
    # 没有就创建
    if not db_user:
        db_user = GuildUserRecord.create(
            user_id=guild_user.user.id,
            nick_name=guild_user.nick,
            joined_time=guild_user.joined_at,
        )
    else:
        # 更新last_speak_time
        db_user.last_speak_time = datetime.now()
        db_user.save()
        # 如果数据库字段与获取的数据不同就更新字段
        if db_user.nick_name != guild_user.nick:
            db_user.nick_name = guild_user.nick
            db_user.save()

    # 记录身分组信息
    for per_user_role in user_roles:
        db_role: Union[GuildRoleRecord, None] = GuildRoleRecord.get_or_none(
            GuildRoleRecord.role_id == per_user_role.id
        )
        if not db_role:
            # 没有就创建
            db_role = GuildRoleRecord.create(
                role_id=per_user_role.id,
                role_name=per_user_role.name,
                color_hex_decimal=per_user_role.color,
            )
        else:
            # 如果数据库字段与获取的数据不同就更新字段
            if db_role.role_name != per_user_role.name:
                db_role.role_name = per_user_role.name
                db_role.save()
            if db_role.color_hex_decimal != per_user_role.color:
                db_role.color_hex_decimal = per_user_role.color
                db_role.save()

        # 记录用户-身份组映射
        db_ur_mapping: Union[UserRoleMapping, None] = UserRoleMapping.get_or_none(
            (UserRoleMapping.user == db_user) & (UserRoleMapping.role == db_role)
        )
        # 没有就创建
        if not db_ur_mapping:
            db_ur_mapping = UserRoleMapping.create(user=db_user, role=db_role)

    if images:
        image_urls: str = "\n".join(images)
    else:
        image_urls = None
    message = GuildMessageRecord(
        message_id=message_id,
        text=text if text else None,
        image=image_urls,
        user=db_user,
        channel=db_channel,
    )
    message.save()


def get_channels_by_threshold_in_period(
    threshold: int, start_time: datetime, end_time: datetime
) -> list[str] | list:
    """
    查找消息数符合条件的子频道的channel_id，无符合条件的子频道时返回空列表
    """
    msg_count_threshold = threshold
    blacklist_users = get_config()["wordcloud"]["blacklist_user_ids"]
    query = (
        GuildMessageRecord.select(
            GuildMessageRecord.channel,
            fn.COUNT(GuildMessageRecord.channel).alias("count"),
        )
        .join_from(
            GuildMessageRecord,
            GuildUserRecord,
            on=(GuildMessageRecord.user == GuildUserRecord.id),
        )
        .join_from(
            GuildMessageRecord,
            ChannelRecord,
            on=(GuildMessageRecord.channel == ChannelRecord.id),
        )
        .where(
            (GuildMessageRecord.received_time > start_time)
            & (GuildMessageRecord.received_time < end_time)
            & (GuildUserRecord.user_id.not_in(blacklist_users))
            & (GuildMessageRecord.text.is_null(False))
        )
        .group_by(GuildMessageRecord.channel)
        .having(fn.COUNT(GuildMessageRecord.channel) > msg_count_threshold)
    )
    log_prompts = [f"{msg.channel.channel_name} {msg.count}" for msg in query]
    logger.info("\n".join(log_prompts))
    return [msg.channel.channel_id for msg in query]


def get_messages_by_channel_in_period(
    channel_id: Union[str, int], start_time: datetime, end_time: datetime
) -> Optional[list[str]]:
    """
    查找指定的 channel_id 的子频道对应的时间段内的文字消息

    当 channel_id 等于 0 时，查找所有子频道记录
    """
    import operator

    expressions = [
        (GuildMessageRecord.received_time > start_time),
        (GuildMessageRecord.received_time < end_time),
    ]

    blacklist_users = get_config()["wordcloud"]["blacklist_user_ids"]
    expressions.append(GuildUserRecord.user_id.not_in(blacklist_users))
    if channel_id != 0:
        expressions.append(ChannelRecord.channel_id == channel_id)
    else:
        blacklist_channels = get_config()["wordcloud"]["blacklist_channels"]
        expressions.append(ChannelRecord.channel_id.not_in(blacklist_channels))

    query = (
        GuildMessageRecord.select()
        .join_from(
            GuildMessageRecord,
            ChannelRecord,
            on=(GuildMessageRecord.channel == ChannelRecord.id),
        )
        .join_from(
            GuildMessageRecord,
            GuildUserRecord,
            on=(GuildMessageRecord.user == GuildUserRecord.id),
        )
        .where(reduce(operator.and_, expressions))
    )
    messages = [msg.text for msg in query if msg.text]
    return messages if len(messages) > 0 else None


def get_messages_by_user(user_id: str) -> Optional[list[str]]:
    """查找指定 user_id 对应用户的所有消息"""
    blacklist_channels = get_config()["wordcloud"]["blacklist_channels"]
    query = (
        GuildMessageRecord.select()
        .join_from(
            GuildMessageRecord,
            GuildUserRecord,
            on=(GuildMessageRecord.user == GuildUserRecord.id),
        )
        .join_from(
            GuildMessageRecord,
            ChannelRecord,
            on=(GuildMessageRecord.channel == ChannelRecord.id),
        )
        .where(
            ChannelRecord.channel_id.not_in(blacklist_channels)
            & (GuildUserRecord.user_id == user_id)
        )
    )
    messages = [msg.text for msg in query if msg.text]
    return messages if len(messages) > 0 else None


def get_messages_by_role(role_id: str) -> Optional[list[str]]:
    """查找指定 role_id 对应身分组的所有消息"""
    blacklist_channels = get_config()["wordcloud"]["blacklist_channels"]
    query = (
        GuildMessageRecord.select()
        .join_from(
            GuildMessageRecord,
            ChannelRecord,
            on=(GuildMessageRecord.channel == ChannelRecord.id),
        )
        .join(GuildUserRecord, on=(GuildMessageRecord.user == GuildUserRecord.id))
        .join(UserRoleMapping, on=(UserRoleMapping.user == GuildUserRecord.id))
        .join(GuildRoleRecord, on=(UserRoleMapping.role == GuildRoleRecord.id))
        .where(
            ChannelRecord.channel_id.not_in(blacklist_channels)
            & (GuildRoleRecord.role_id == role_id)
        )
    )
    messages = [msg.text for msg in query if msg.text]
    return messages if len(messages) > 0 else None


def get_all_channels() -> list[str]:
    """查找所有子频道记录，返回排序好的子频道id(升序)"""
    query = ChannelRecord.select()
    raw_channels = [(channel.channel_id, channel.position) for channel in query]
    sorted_channels = sorted(raw_channels, key=lambda x: x[1])
    return [per_channel[0] for per_channel in sorted_channels]


def get_users_by_channel_in_period(
    start_time: datetime, end_time: datetime, channel_id: Optional[str] = None
) -> list[str]:
    """查找指定子频道时间段内所有发过消息的用户id，不传channel_id默认获取时间段内所有用户id"""
    import operator

    expressions = [
        (GuildMessageRecord.received_time > start_time),
        (GuildMessageRecord.received_time < end_time),
    ]
    if channel_id:
        expressions.append(ChannelRecord.channel_id == channel_id)
    query = (
        GuildMessageRecord.select(GuildUserRecord.user_id)
        .join_from(
            GuildMessageRecord,
            ChannelRecord,
            on=(GuildMessageRecord.channel == ChannelRecord.id),
        )
        .join_from(
            GuildMessageRecord,
            GuildUserRecord,
            on=(GuildMessageRecord.user == GuildUserRecord.id),
        )
        .where(reduce(operator.and_, expressions))
    )
    return [msg.user.user_id for msg in query]


def get_joined_time_by_user(user_id: str) -> datetime:
    """查询指定用户的加入时间"""
    query = GuildUserRecord.get(GuildUserRecord.user_id == user_id)
    return datetime.fromisoformat(query.joined_time)


def get_channel_name_by_channel_id(channel_id: str) -> str:
    """查询指定子频道的名称"""
    query = ChannelRecord.get(ChannelRecord.channel_id == channel_id)
    return query.channel_name
