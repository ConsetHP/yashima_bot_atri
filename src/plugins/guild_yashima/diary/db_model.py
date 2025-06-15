"""
数据库模型  ! 需要重构
"""

from datetime import datetime

from peewee import CharField, DateTimeField, BigIntegerField, TextField

from ..database.base import BaseModel


class GuildMessageRecord(BaseModel):
    """频道聊天消息"""

    channel_id = BigIntegerField()
    user_id = CharField()
    content = TextField()
    recv_time = DateTimeField(default=datetime.now, index=True)


class GuildImgRecord(GuildMessageRecord):
    """频道图片url"""

    pass


class QQGuildMessageRecord(
    GuildMessageRecord
):  # 由于 user_id 与 cqhttp 返回的 user_id 不通用，暂时分开存储
    """官方API频道文字消息"""

    pass


class QQGuildImgRecord(GuildMessageRecord):
    """官方API频道图片消息"""

    pass
