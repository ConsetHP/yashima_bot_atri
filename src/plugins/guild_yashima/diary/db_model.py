"""
数据库模型
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
