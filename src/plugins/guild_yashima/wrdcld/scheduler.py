from datetime import timedelta, datetime

from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from nonebot_plugin_apscheduler import scheduler

from .analyzer import get_wordcloud_img
from ..diary.database.operator import (
    get_channels_by_threshold_in_period,
    get_messages_by_channel_in_period,
)
from ..utils import get_config
from ..send import send_msgs
from ..character import atri


@scheduler.scheduled_job("cron", minute="0", hour="4", id="yesterday_wordcloud_job")
async def yesterday_wordcloud_job():
    overall_target_channel = get_config()["wordcloud"]["overall_target_channel"]
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    start_time = yesterday.replace(hour=4, minute=0, second=0, microsecond=0)
    end_time = today.replace(hour=3, minute=59, second=59, microsecond=0)
    msg_count_threshold = int(get_config()["wordcloud"]["generation_threshold"])

    # 生成子频道词云
    channels = get_channels_by_threshold_in_period(
        msg_count_threshold, start_time, end_time
    )
    if len(channels) > 0:
        logger.info(f"以下频道将生成词云：{channels}")
        for channel in channels:
            logger.info(f"开始生成词云，频道ID:{channel}")
            notice = f"{atri.discourse_particle}、そろそろワードクラウドの時間です。{atri.loading}"
            await send_msgs(channel, notice)

            messages = get_messages_by_channel_in_period(channel, start_time, end_time)
            try:
                image = await get_wordcloud_img(messages)
            except Exception as ex:
                logger.warning(f"子频道【{channel}】词云生成失败：{ex}")
                image = None
            else:
                logger.info(f"子频道【{channel}】词云生成成功")
            if image:
                msg = MessageSegment.text(
                    f"{atri.modal_particle}、このチャンネルのワードクラウドがこちらです、{atri.proud}"
                ) + MessageSegment.image(image)
                await send_msgs(channel, msg)
            else:
                logger.warning(f"子频道【{channel}】词云图片未生成")
    else:
        notice = f"{atri.discourse_particle}、そろそろワードクラウドの時間です。{atri.loading}"
        await send_msgs(overall_target_channel, notice)

    # 生成全频词云
    logger.info("开始生成全频道词云")
    messages = get_messages_by_channel_in_period(0, start_time, end_time)
    try:
        image = await get_wordcloud_img(messages)
    except Exception as ex:
        logger.warning(f"全频词云生成失败：{ex}")
    else:
        logger.info("全频词云生成成功")
    if image:
        # 水频（全频词云目标频）在消息未达标时不会生成子频词云，加个判断去掉 おまけに
        bonus_msg = "おまけに" if str(overall_target_channel) in channels else ""
        msg = MessageSegment.text(
            f"{bonus_msg}💎ヤシマ作戦指揮部💎のフルワードクラウドがこちらです、{atri.proud}"
        ) + MessageSegment.image(image)
        await send_msgs(overall_target_channel, msg)
    else:
        logger.warning("全频词云图片未生成")
