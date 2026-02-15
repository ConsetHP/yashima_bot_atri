from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Sequence
from collections import Counter, defaultdict

from peewee import SQL

from ..database.operator import database
from ...config import get_config


class TrendIcon(Enum):
    UP = "⬆️"
    EQUAL = "⏺️"
    DOWN = "⬇️"


class WeekDays(Enum):
    MONDAY = "月曜日"
    TUESDAY = "火曜日"
    WEDNESDAY = "水曜日"
    THURSDAY = "木曜日"
    FRIDAY = "金曜日"
    SATURDAY = "土曜日"
    SUNDAY = "日曜日"


class ReportAnalyzer:
    def __init__(self):
        self.weekdays_nums_map = {
            0: WeekDays.MONDAY.value,
            1: WeekDays.TUESDAY.value,
            2: WeekDays.WEDNESDAY.value,
            3: WeekDays.THURSDAY.value,
            4: WeekDays.FRIDAY.value,
            5: WeekDays.SATURDAY.value,
            6: WeekDays.SUNDAY.value,
        }

    def _deserialize_msg_and_get_type(self, raw_msg: str) -> str:
        import json

        # TODO: 同一条消息可能存在图文混排的情况，需要额外处理，而不是拿第一个segment
        msg = json.loads(raw_msg)
        try:
            msg_type = msg[0]["type"]
        except KeyError:
            if msg[0].get("messages") is not None:
                # 合并转发消息，需要另外处理
                msg_type = "text"
            else:
                raise KeyError(f"Invalid msg: {msg}")
        return msg_type

    def analyze_busiest_time_today(self) -> int:
        """今日消息数最多的时间段"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59)
        query = database.get_grouped_message_counts_by_time(
            today_start, today_end
        ).order_by(SQL("count").desc())
        return int(query.first().hour)

    def analyze_average_message_in_week(
        self, week_start: datetime, week_end: datetime
    ) -> int:
        """一周内每日消息的平均值"""
        query = database.get_grouped_message_counts_by_time(
            week_start, week_end, delta=timedelta(days=1)
        )
        total_count = 0
        for per_day in query:
            total_count += per_day.count
        return int(total_count / 7)

    def analyze_active_users_today(self) -> int:
        """今日消息数最多的用户"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59)
        query = database.get_active_group_user_between(
            today_start, today_end, group_id=str(get_config().analyzer.target_group)
        )
        return query.count()

    def get_message_type_counts_between(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: Optional[timedelta] = None,
    ) -> Sequence[Optional[Counter]]:
        import math

        if group_by:
            # dicts()能避免实例化，速度应该快点
            messages = database.get_labeled_message_content_by_time(
                start_time, end_time, group_by
            ).dicts()

            # sort messages into groups
            grouped_msgs = defaultdict(list)
            for per_msg in messages:
                grouped_msgs[per_msg["hour"]].append(
                    self._deserialize_msg_and_get_type(per_msg["content"])
                )

            group_count = math.ceil((end_time - start_time) / group_by)
            hour_keys = [f"{i:02d}" for i in range(group_count)]
            message_type_counts = []
            for per_key in hour_keys:
                if len(grouped_msgs[per_key]) == 0:
                    message_type_counts.append(None)
                    continue
                message_type_counts.append(Counter(grouped_msgs[per_key]))

        else:
            messages = database.get_group_message_between(start_time, end_time).dicts()

            message_type_counts = [
                Counter(
                    self._deserialize_msg_and_get_type(per_message["content"])
                    for per_message in messages
                )
            ]
        return message_type_counts

    def get_message_count_between(
        self, start_time: datetime, end_time: datetime
    ) -> str:
        return str(database.get_group_message_between(start_time, end_time).count())

    def calculate_trend_percentage(self, previous_count: int, last_count: int) -> int:
        return int((previous_count / last_count - 1) * 100)

    def get_trend_icon(self, trend_percentage: int, approximate_threshold: int) -> str:
        if trend_percentage > approximate_threshold:
            trend_icon = TrendIcon.UP.value
        elif (
            trend_percentage <= approximate_threshold
            and trend_percentage >= -approximate_threshold
        ):
            trend_icon = TrendIcon.EQUAL.value
        else:
            trend_icon = TrendIcon.DOWN.value
        return trend_icon
