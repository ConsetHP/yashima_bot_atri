from dataclasses import dataclass
from datetime import time
from typing import Any, Literal, NamedTuple, NewType

from httpx import URL
from pydantic import BaseModel

RawPost = Any
Target = NewType("Target", str)
Category = int
Tag = str


@dataclass(eq=True, frozen=True)
class User:
    user: int
    user_type: Literal["group", "private"]


@dataclass(eq=True, frozen=True)
class PlatformTarget:
    target: str
    platform_name: str
    target_name: str


class ChannelSubInfo(NamedTuple):
    channel_id: int
    categories: list[Category]
    tags: list[Tag]


class TimeWeightConfig(BaseModel):
    start_time: time
    end_time: time
    weight: int


class WeightConfig(BaseModel):
    default: int
    time_config: list[TimeWeightConfig]


class PlatformWeightConfigResp(BaseModel):
    target: Target
    target_name: str
    platform_name: str
    weight: WeightConfig


class ApiError(Exception):
    def __init__(self, url: URL) -> None:
        msg = f"api {url} error"
        super().__init__(msg)


class SubUnit(NamedTuple):
    sub_target: Target
    channel_sub_infos: list[ChannelSubInfo]
