"""
数据库操作
"""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Union, List

from peewee import IntegrityError

from ..types import Category, Tag, ChannelSubInfo
from ..types import Target as T_Target
from .model import (
    GuildSubscribedChannel,
    SubscribeTarget,
    Subscribe,
)
from ...database.base import db


class SubscribeDupException(Exception): ...


class NoSuchTargetException(Exception): ...


class DBOperator:
    def __init__(self):
        self.add_target_hook: List[Callable[[str, T_Target], Awaitable]] = []
        self.delete_target_hook: List[Callable[[str, T_Target], Awaitable]] = []

    def register_add_target_hook(self, func: Callable[[str, T_Target], Awaitable]):
        self.add_target_hook.append(func)

    def register_delete_target_hook(self, func: Callable[[str, T_Target], Awaitable]):
        self.delete_target_hook.append(func)

    @db.atomic()
    async def add_subscribe(
        self,
        channel_id: int,
        target: T_Target,  # 订阅的账号id
        target_name: str,  # 订阅的账号名
        platform_name: str,
        cats: List[Category],
        tags: List[Tag],
    ):
        """添加订阅"""
        db_channel: Union[GuildSubscribedChannel, None] = (
            GuildSubscribedChannel.get_or_none(
                GuildSubscribedChannel.channel_id == channel_id
            )
        )
        if not db_channel:
            db_channel = GuildSubscribedChannel.create(channel_id=channel_id)

        db_target: Union[SubscribeTarget, None] = SubscribeTarget.get_or_none(
            (SubscribeTarget.platform_name == platform_name)
            & (SubscribeTarget.target == target)
        )
        if not db_target:
            db_target = SubscribeTarget.create(
                target=target,
                platform_name=platform_name,
                target_name=target_name,
            )
            await asyncio.gather(
                *[hook(platform_name, target) for hook in self.add_target_hook]
            )
        else:
            db_target.target_name = target_name  # 更新订阅目标昵称
            db_target.save()

        subscribe = Subscribe(
            categories=cats, tags=tags, subscribed_channel=db_channel, target=db_target
        )
        try:
            subscribe.save()
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise SubscribeDupException()
            raise e

    @db.atomic()
    async def list_subscribe(self, channel_id: int) -> Sequence[Subscribe]:
        """获取特定频道的订阅数据"""
        query = (
            Subscribe.select(Subscribe, GuildSubscribedChannel, SubscribeTarget)
            # 关联 GuildSubscribedChannel 表
            .join(
                GuildSubscribedChannel,
                on=(Subscribe.subscribed_channel == GuildSubscribedChannel.id),
            )
            .switch(Subscribe)
            # 关联 SubscribeTarget 表
            .join(SubscribeTarget, on=(Subscribe.target == SubscribeTarget.id))
            .where(GuildSubscribedChannel.channel_id == channel_id)  # 匹配频道id
        )
        return list(query)

    @db.atomic()
    async def list_subs_with_all_info(self) -> Sequence[Subscribe]:
        """获取数据库中所有频道的订阅数据"""
        query = (
            Subscribe.select(Subscribe, GuildSubscribedChannel, SubscribeTarget)
            .join(
                GuildSubscribedChannel,
                on=(Subscribe.subscribed_channel == GuildSubscribedChannel.id),
            )
            .switch(Subscribe)
            .join(SubscribeTarget, on=(Subscribe.target == SubscribeTarget.id))
        )
        return list(query)

    @db.atomic()
    async def del_subscribe(self, channel_id: int, target: str, platform_name: str):
        """删除订阅数据"""
        user_obj = GuildSubscribedChannel.get_or_none(
            GuildSubscribedChannel.channel_id == channel_id
        )
        target_obj = SubscribeTarget.get_or_none(
            (SubscribeTarget.platform_name == platform_name)
            & (SubscribeTarget.target == target)
        )
        if user_obj and target_obj:
            Subscribe.delete().where(
                (Subscribe.subscribed_channel == user_obj.id)
                & (Subscribe.target == target_obj.id)
            ).execute()

            # 清理没有被订阅的目标
            target_count = (
                Subscribe.select().where(Subscribe.target == target_obj.id).count()
            )
            if target_count == 0:
                SubscribeTarget.delete().where(
                    (SubscribeTarget.platform_name == platform_name)
                    & (SubscribeTarget.target == target)
                ).execute()
                await asyncio.gather(
                    *[
                        hook(platform_name, T_Target(target))
                        for hook in self.delete_target_hook
                    ]
                )

            # 清理没有订阅的子频道
            channel_count = (
                Subscribe.select()
                .where(Subscribe.subscribed_channel == user_obj.id)
                .count()
            )
            if channel_count == 0:
                GuildSubscribedChannel.delete().where(
                    GuildSubscribedChannel.channel_id == channel_id
                ).execute()

    @db.atomic()
    async def get_platform_target(
        self, platform_name: str
    ) -> Sequence[SubscribeTarget]:
        """获取指定平台的所有被订阅目标"""
        query = SubscribeTarget.select().where(
            SubscribeTarget.platform_name == platform_name
        )
        return list(query)

    @db.atomic()
    async def get_current_weight_val(self, platform_list: list[str]) -> dict[str, int]:
        """获取当前权重值"""
        res = {}
        # cur_time = _get_time()
        with db.atomic():
            targets = SubscribeTarget.select(
                SubscribeTarget.platform_name,
                SubscribeTarget.default_schedule_weight,
                SubscribeTarget.target,
            ).where(SubscribeTarget.platform_name.in_(platform_list))
            for target in targets:
                key = f"{target.platform_name}-{target.target}"
                weight = target.default_schedule_weight
                res[key] = weight
        return res

    @db.atomic()
    async def get_platform_target_subscribers(
        self, platform_name: str, target: T_Target
    ) -> list[ChannelSubInfo]:
        """获取指定平台的被订阅目标信息"""
        query = (
            Subscribe.select(Subscribe, GuildSubscribedChannel, SubscribeTarget)
            .join(SubscribeTarget, on=(Subscribe.target == SubscribeTarget.id))
            .where(
                (SubscribeTarget.platform_name == platform_name)
                & (SubscribeTarget.target == target)
            )
            .join(
                GuildSubscribedChannel,
                on=(Subscribe.subscribed_channel == GuildSubscribedChannel.id),
            )
        )
        return [
            ChannelSubInfo(
                subscribe.subscribed_channel.channel_id,
                subscribe.categories,
                subscribe.tags,
            )
            for subscribe in query
        ]

    @db.atomic()
    async def clear_db(self):
        """清空数据库，用于单元测试清理环境"""
        GuildSubscribedChannel.delete().execute()
        SubscribeTarget.delete().execute()
        # ScheduleTimeWeight.delete().execute()
        Subscribe.delete().execute()


database = DBOperator()
