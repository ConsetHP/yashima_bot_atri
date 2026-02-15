from enum import StrEnum

from pydantic import BaseModel, Field


class AdapterName(StrEnum):
    one_bot_v11 = "OneBot V11"
    qq = "QQ"


class SendTarget(BaseModel):
    adapter: AdapterName
    bot_id: str


class TargetQQGroup(SendTarget):
    adapter: AdapterName = Field(default=AdapterName.one_bot_v11)
    bot_id: str
    group_id: int


class TargetQQGuildOB11(SendTarget):
    adapter: AdapterName = Field(default=AdapterName.one_bot_v11)
    bot_id: str
    guild_id: str
    channel_id: str


class TargetQQGuildOfficial(SendTarget):
    adapter: AdapterName = Field(default=AdapterName.qq)
    bot_id: str
    channel_id: str
