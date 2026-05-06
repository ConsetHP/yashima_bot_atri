from enum import StrEnum

from pydantic import BaseModel, Field


class AdapterName(StrEnum):
    one_bot_v11 = "OneBot V11"
    qq = "QQ"


class SendTarget(BaseModel):
    bot_id: str
    adapter: AdapterName


class TargetQQGroup(SendTarget):
    bot_id: str
    group_id: int
    adapter: AdapterName = Field(default=AdapterName.one_bot_v11)


class TargetQQGuildOB11(SendTarget):
    bot_id: str
    guild_id: str
    channel_id: str
    adapter: AdapterName = Field(default=AdapterName.one_bot_v11)


class TargetQQGuildOfficial(SendTarget):
    bot_id: str
    channel_id: str
    adapter: AdapterName = Field(default=AdapterName.qq)
