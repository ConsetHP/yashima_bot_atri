"""
数据库模型
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from peewee import (
    CharField,
    DateTimeField,
    IntegerField,
)

from ..database.base import BaseModel


class ClockEventLog(BaseModel):
    """打卡记录"""

    user_name = CharField()
    user_id = CharField(index=True)
    status = CharField()  # 打卡状态：参考 ClockStatus
    start_time = DateTimeField(default=datetime.now)
    end_time = DateTimeField(null=True)
    duration = IntegerField(default=0)  # 持续时长，单位分钟

    def update_duration(self) -> int:
        """计算并更新持续时长"""
        if not self.start_time or not self.end_time:
            raise ValueError("start or end time is None")
        self.duration = int((self.end_time - self.start_time).total_seconds() / 60)
        return self.duration

    def duration_desc(self) -> str:
        return ClockEventLog.to_duration_desc(self.duration)

    @staticmethod
    def to_duration_desc(duration: int) -> str:
        hour = int(duration / 60)
        minute = duration % 60
        if hour > 0:
            return f"{hour}小时{minute}分"
        else:
            return f"{minute}分钟"

    @staticmethod
    def query_by_user_id_and_status(
        user_id: str, status: "ClockStatus"
    ) -> Optional["ClockEventLog"]:
        return (
            ClockEventLog.select()
            .where(
                (ClockEventLog.status == status.value)
                & (ClockEventLog.user_id == user_id)
            )
            .order_by(ClockEventLog.id.desc())
            .limit(1)
            .get_or_none()
        )

    @staticmethod
    def query_overtime(user_id: str) -> Optional["ClockEventLog"]:
        return ClockEventLog.query_by_user_id_and_status(user_id, ClockStatus.OVERTIME)

    @staticmethod
    def query_working(user_id: str) -> Optional["ClockEventLog"]:
        return ClockEventLog.query_by_user_id_and_status(user_id, ClockStatus.WORKING)


class ClockStatus(Enum):
    WORKING = "working"  # 进行中
    FINISH = "finish"  # 已结束
    OVERTIME = "overtime"  # 超时自动签退
