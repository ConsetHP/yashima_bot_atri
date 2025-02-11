import asyncio
from datetime import datetime, timedelta

import pandas as pd
from nonebot.log import logger

from .db_operator import get_user_ids_by_channel_and_time
from .utils import remove_duplicates, get_days_since_joined, get_channel_name


async def get_seniority_by_channel(channel_id: int):
    last_month = datetime.now() - timedelta(days=8)
    yesterday = datetime.now() - timedelta(days=1)
    start_time = last_month.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    raw_user_ids = get_user_ids_by_channel_and_time(channel_id, start_time, end_time)
    user_ids = remove_duplicates(raw_user_ids)
    logger.info(f"start downloading: {channel_id}")
    joined_days = await asyncio.gather(*[get_days_since_joined(id) for id in user_ids])
    seniority = []
    for days in joined_days:
        if days <= 30:
            seniority.append("noob")
        elif days <= 100:
            seniority.append("junior")
        elif days <= 300:
            seniority.append("senior")
        elif days <= 600:
            seniority.append("pro")
        elif days <= 1000:
            seniority.append("master")
        else:
            seniority.append("supreme")
    return seniority


async def get_seniority_dataframe(channel_ids: list[int]):
    channel_names, seniorities = [], []
    logger.info(f"以下频道将生成表格：{channel_ids}")
    for per_channel in channel_ids:
        seniority = await get_seniority_by_channel(per_channel)
        raw_channel_name = await get_channel_name(per_channel)
        previous_channel_name = (
            raw_channel_name
            if len(raw_channel_name) < 6
            else f"{raw_channel_name[:6]}..."
        )
        previous_channel_names = [previous_channel_name] * len(seniority)
        channel_names += previous_channel_names
        seniorities += seniority
    data = pd.DataFrame({"channel_name": channel_names, "seniority": seniorities})
    return data
