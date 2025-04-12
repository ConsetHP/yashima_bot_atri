"""
数据库模型
"""

from datetime import datetime

from peewee import (
    CharField,
    BigIntegerField,
    BooleanField,
    IntegerField,
    TextField,
    ForeignKeyField,
    DateTimeField,
)

from ...database.base import BaseModel


class ThreadUser(BaseModel):
    """使用了一键发帖服务的用户"""

    user_id = CharField(unique=True)
    last_request_id = IntegerField()
    last_request_time = DateTimeField(default=datetime.now, index=True)


class ThreadInfo(BaseModel):
    """帖子具体信息"""

    user = ForeignKeyField(ThreadUser, backref="infos", on_delete="CASCADE")
    source_channel_id = BigIntegerField()
    text = TextField()
    notify = BooleanField()
    request_id = IntegerField()
    recv_time = DateTimeField(default=datetime.now, index=True)


class Thread(BaseModel):
    """帖子记录"""

    title = TextField()
    thread_id = TextField()
    thread_channel_id = BigIntegerField()
    info = ForeignKeyField(ThreadInfo, backref="threads", on_delete="CASCADE")
    user = ForeignKeyField(ThreadUser, backref="threads", on_delete="CASCADE")


class ThreadNotFoundError(Exception): ...


class UserNotFoundError(Exception): ...


class AddThreadError(Exception): ...
