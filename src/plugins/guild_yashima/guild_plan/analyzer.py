from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from nonebot.log import logger

from .utils import remove_duplicates, get_days_since_joined
from ..diary.database.operator import (
    get_users_by_channel_in_period,
    get_channel_name_by_channel_id,
)


def get_user_seniorities_by_channel(channel_id: Optional[str] = None) -> list[str]:
    """获取指定子频道的用户加入时间，不传channel_id默认获取所有频道的用户加入时间"""
    last_week = datetime.now() - timedelta(days=8)
    previous_time = datetime.now()
    start_time = last_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = previous_time.replace(hour=23, minute=59, second=59, microsecond=0)
    raw_user_ids = get_users_by_channel_in_period(
        channel_id=channel_id, start_time=start_time, end_time=end_time
    )
    user_ids = remove_duplicates(raw_user_ids)
    joined_days: list[int] = [get_days_since_joined(per_id) for per_id in user_ids]
    user_seniorities: list[str] = []
    for days in joined_days:
        if days <= 30:
            user_seniorities.append("[0, 30]")
        elif days <= 100:
            user_seniorities.append("(30, 100]")
        elif days <= 300:
            user_seniorities.append("(100, 300]")
        elif days <= 600:
            user_seniorities.append("(300, 600]")
        elif days <= 1000:
            user_seniorities.append("(600, 1000]")
        else:
            user_seniorities.append("(1000, ∞]")
    return user_seniorities


def build_user_seniorities_dataframe(channel_ids: Optional[list[str]] = None):
    """构造pandas的Dataframe，channel_ids为None时使用所有子频道合并的数据"""
    channel_names, seniorities = [], []
    if not channel_ids:
        channel_ids: list[int] = [0]
    logger.info(f"以下频道将生成表格：{channel_ids}")
    for per_channel in channel_ids:
        if per_channel != 0:
            user_seniorities: list[str] = get_user_seniorities_by_channel(per_channel)
            raw_channel_name = get_channel_name_by_channel_id(per_channel)
            formatted_channel_name = (
                raw_channel_name
                if len(raw_channel_name) < 6
                else f"{raw_channel_name[:6]}..."
            )
        else:
            user_seniorities: list[str] = get_user_seniorities_by_channel()
            channel_name = "所有子频道"
            formatted_channel_name = channel_name
        formatted_channel_names = [formatted_channel_name] * len(user_seniorities)
        channel_names += formatted_channel_names
        seniorities += user_seniorities
    data = pd.DataFrame({"channel_name": channel_names, "joined_days": seniorities})
    return data
