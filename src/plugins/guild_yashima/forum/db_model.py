"""
数据库模型
"""

from peewee import (
    CharField,
    BigIntegerField,
    BooleanField,
    IntegerField,
    TextField,
    ForeignKeyField,
    DateTimeField,
    SQL,
)

from ..database.base import BaseModel


class ThreadContent(BaseModel):
    """帖子具体内容"""

    title = TextField()
    text_content = TextField(default="")
    image_url = TextField(default="")
    need_notice = BooleanField(default=True)
    recv_time = DateTimeField()
    record_id = IntegerField(max_length=3)


class ThreadUser(BaseModel):
    """使用了一键发帖服务的用户"""

    user_id = CharField()
    channel_id = BigIntegerField()
    last_record_id = IntegerField(max_length=3)

    class Meta:
        constraints = [SQL("UNIQUE (channel_id, user_id)")]


class ThreadRecord(BaseModel):
    """帖子记录"""

    channel_id = BigIntegerField()
    thread_id = TextField()
    content = ForeignKeyField(ThreadContent, backref="threads", on_delete="CASCADE")
    user = ForeignKeyField(ThreadUser, backref="threads", on_delete="CASCADE")
