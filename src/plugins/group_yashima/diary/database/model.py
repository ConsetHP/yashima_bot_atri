from datetime import datetime, timedelta
from peewee import (
    CharField,
    DateTimeField,
    BigIntegerField,
    TextField,
    ForeignKeyField,
)

from ...database import BaseModel, register_table


def three_days_later():
    """3天后"""
    return datetime.now() + timedelta(days=3)


def a_month_later():
    """30天后"""
    return datetime.now() + timedelta(days=30)


@register_table
class QQUser(BaseModel):
    user_id = CharField(unique=True, index=True)
    nickname = TextField()
    sex = TextField()
    age = BigIntegerField()
    expire_time = DateTimeField(default=three_days_later)


@register_table
class GroupUser(BaseModel):
    group_id = CharField()
    user = ForeignKeyField(QQUser, backref="groupusers", on_delete="CASCADE")
    nickname = TextField()  # 群昵称
    joined_time = DateTimeField()
    last_sent_time = DateTimeField()
    extra_data = TextField()  # 相对次要但未来可能会用上的字段
    expire_time = DateTimeField(default=three_days_later)


@register_table
class Group(BaseModel):
    group_id = CharField(unique=True, index=True)
    group_name = TextField()
    group_create_time = DateTimeField()
    extra_data = TextField()  # 相对次要但未来可能会用上的字段
    expire_time = DateTimeField(default=a_month_later)


@register_table
class GroupMessage(BaseModel):
    message_id = CharField()
    content = TextField(null=True)  # 包含text, image, face等内容的json
    user = ForeignKeyField(GroupUser, backref="messages", on_delete="CASCADE")
    group = ForeignKeyField(Group, backref="messages", on_delete="CASCADE")
    record_time = DateTimeField(default=datetime.now, index=True)
