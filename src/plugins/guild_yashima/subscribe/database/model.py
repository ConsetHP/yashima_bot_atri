"""
数据库模型
"""

from peewee import (
    CharField,
    IntegerField,
    BigIntegerField,
    TextField,
    ForeignKeyField,
    TimeField,
    SQL,
)

from ...database.base import BaseModel


class GuildSubscribedChannel(BaseModel):
    """订阅了平台消息的子频道"""

    channel_id = BigIntegerField()


class SubscribeTarget(BaseModel):
    """订阅的目标账号"""

    platform_name = CharField(max_length=20)
    target = CharField(max_length=1024)
    target_name = CharField(max_length=1024)
    default_schedule_weight = IntegerField(default=10)

    class Meta:
        constraints = [SQL("UNIQUE (platform_name, target)")]


class ScheduleTimeWeight(BaseModel):
    target = ForeignKeyField(
        SubscribeTarget, backref="time_weight", on_delete="CASCADE"
    )
    start_time = TimeField()
    end_time = TimeField()
    weight = IntegerField()


class Subscribe(BaseModel):
    target = ForeignKeyField(SubscribeTarget, backref="subscribes", on_delete="CASCADE")
    subscribed_channel = ForeignKeyField(
        GuildSubscribedChannel, backref="subscribes", on_delete="CASCADE"
    )
    categories = TextField()  # 贴文类别
    tags = TextField()  # 贴文标签

    class Meta:
        constraints = [SQL("UNIQUE (target_id, subscribed_channel_id)")]
