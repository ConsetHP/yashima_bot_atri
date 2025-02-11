from datetime import datetime

from ..diary.db_model import GuildMessageRecord, GuildImgRecord


def get_user_ids_by_channel_and_time(
    channel_id: int, start_time: datetime, end_time: datetime
):
    msg_query = GuildMessageRecord.select(GuildMessageRecord.user_id).where(
        (GuildMessageRecord.channel_id == channel_id)
        & (GuildMessageRecord.recv_time >= start_time)
        & (GuildMessageRecord.recv_time <= end_time)
    )
    img_query = GuildImgRecord.select(GuildImgRecord.user_id).where(
        (GuildImgRecord.channel_id == channel_id)
        & (GuildImgRecord.recv_time >= start_time)
        & (GuildImgRecord.recv_time <= end_time)
    )

    msg_user_ids = [record.user_id for record in msg_query]
    img_user_ids = [record.user_id for record in img_query]
    total_user_ids = msg_user_ids + img_user_ids
    return total_user_ids
