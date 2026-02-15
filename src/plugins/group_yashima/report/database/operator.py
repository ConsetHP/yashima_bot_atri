from datetime import datetime, timedelta

from peewee import ModelSelect, fn

from ...diary.database.model import GroupMessage, GroupUser


class DBOperator:
    def get_group_message_between(
        self, start_time: datetime, end_time: datetime
    ) -> ModelSelect:
        import operator
        from functools import reduce

        expressions = [
            (GroupMessage.record_time >= start_time),
            (GroupMessage.record_time < end_time),
        ]
        return GroupMessage.select().where(
            reduce(operator.and_, expressions)
        )  # TODO: 添加group参数，只获取指定群的消息

    def _validate_delta(
        self, start_time: datetime, end_time: datetime, delta: timedelta
    ) -> str:
        if delta == timedelta(hours=1):
            time_format = r"%H"
        elif delta == timedelta(days=1):
            time_format = r"%d"
        else:
            raise ValueError("只支持按1小时或1天分段")
        total_time = end_time - start_time
        if delta > total_time:
            raise ValueError("delta不可大于总时间段")
        return time_format

    def get_grouped_message_counts_by_time(
        self,
        start_time: datetime,
        end_time: datetime,
        delta: timedelta = timedelta(hours=1),
    ) -> ModelSelect:
        time_format = self._validate_delta(start_time, end_time, delta)
        return (
            GroupMessage.select(
                fn.strftime(time_format, GroupMessage.record_time).alias("hour"),
                fn.COUNT(GroupMessage.id).alias("count"),
            )
            .where(
                (GroupMessage.record_time >= start_time)
                & (GroupMessage.record_time < end_time)
            )
            .group_by(fn.strftime(time_format, GroupMessage.record_time))
        )

    def get_labeled_message_content_by_time(
        self,
        start_time: datetime,
        end_time: datetime,
        delta: timedelta = timedelta(hours=1),
    ) -> ModelSelect:
        time_format = self._validate_delta(start_time, end_time, delta)
        return (
            GroupMessage.select(
                fn.strftime(time_format, GroupMessage.record_time).alias("hour"),
                GroupMessage.content,
            )
            .where(
                (GroupMessage.record_time >= start_time)
                & (GroupMessage.record_time < end_time)
            )
            .order_by(GroupMessage.record_time)
        )

    def get_active_group_user_between(
        self,
        start_time: datetime,
        end_time: datetime,
        group_id: str,
    ) -> ModelSelect:
        # 不能依赖 GroupUser.last_sent_time 来判断，因为 GroupUser 信息不会及时更新
        # 虽然user确实按照条件筛选，但是要注意user.messages是user的所有message，backref不会被筛选
        return (
            GroupUser.select()
            .join(GroupMessage)
            .where(
                (GroupMessage.record_time >= start_time)
                & (GroupMessage.record_time < end_time)
                & (GroupUser.group_id == group_id)
            )
            .distinct()
        )


database = DBOperator()
