from datetime import datetime

from peewee import (
    CharField,
    DateTimeField,
    BigIntegerField,
    TextField,
    ForeignKeyField,
    SQL,
)

from ...database.base import BaseModel


class GuildRoleRecord(BaseModel):
    """频道身份组"""

    role_id = CharField(unique=True)
    role_name = TextField()
    color_hex_decimal = TextField()  # ARGB的HEX十六进制颜色值转换后的十进制数值


class GuildUserRecord(BaseModel):
    """频道用户"""

    user_id = CharField(unique=True)
    nick_name = TextField()
    joined_time = DateTimeField()
    last_speak_time = DateTimeField(default=datetime.now)


class ChannelRecord(BaseModel):
    """子频道详情"""

    channel_id = CharField()
    guild_id = CharField()
    channel_name = TextField()
    position = BigIntegerField()


class UserRoleMapping(BaseModel):
    """用户-身分组映射表"""

    user = ForeignKeyField(GuildUserRecord, backref="roles", on_delete="CASCADE")
    role = ForeignKeyField(GuildRoleRecord, backref="users", on_delete="CASCADE")

    class Meta:
        constraints = [SQL("UNIQUE (user, role)")]


class GuildMessageRecord(BaseModel):
    """频道聊天消息"""

    message_id = CharField()
    text = TextField(null=True)
    image = TextField(null=True)
    user = ForeignKeyField(GuildUserRecord, backref="messages", on_delete="CASCADE")
    channel = ForeignKeyField(ChannelRecord, backref="messages", on_delete="CASCADE")
    received_time = DateTimeField(default=datetime.now, index=True)
