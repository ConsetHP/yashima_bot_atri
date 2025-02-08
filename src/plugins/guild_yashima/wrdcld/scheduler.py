from datetime import timedelta, datetime

from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from nonebot_plugin_apscheduler import scheduler

from .db_operator import query_wordcloud_generatable_channel_ids, get_wordcloud_by_time
from .analyzer import get_wordcloud_img
from ..utils import get_config
from ..send import send_msgs
from ..character import Atri


@scheduler.scheduled_job("cron", minute="10", hour="0", id="yesterday_wordcloud_job")
async def yesterday_wordcloud_job():
    try:
        overall_target_channel = get_config()["wordcloud"]["overall_target_channel"]
        debug_channel = get_config()["debug"]["test_channel_id"]
        disabled_channels = get_config()["wordcloud"]["disabled_channels"]
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
        channels = query_wordcloud_generatable_channel_ids(start_time, end_time)
        if len(channels) > 0:
            logger.info(f"以下频道将生成词云：{channels}")
            for channel in channels:
                # 检查该子频道是否已禁用词云生成
                if channel in disabled_channels:
                    continue

                logger.info(f"开始生成词云，频道ID:{channel}")

                notice = f"{Atri.general_word('discourse_particle')}、そろそろワードクラウドの時間です。{Atri.general_word('loading')}"
                await send_msgs(channel, notice)

                messages = await get_wordcloud_by_time(channel, start_time, end_time)
                image = await get_wordcloud_img(messages)
                if image:
                    msg = MessageSegment.text(
                        f"{Atri.general_word('modal_particle')}、このチャンネルのワードクラウドがこちらです、{Atri.general_word('proud')}"
                    ) + MessageSegment.image(image)
                    await send_msgs(channel, msg)
                else:
                    logger.error("全频道词云图片未生成")
                    raise Exception("词云图片未生成")
        else:
            notice = f"{Atri.general_word('discourse_particle')}、そろそろワードクラウドの時間です。{Atri.general_word('loading')}"
            await send_msgs(overall_target_channel, notice)

        logger.info("开始生成全频道词云")
        messages = await get_wordcloud_by_time(0, start_time, end_time)
        image = await get_wordcloud_img(messages)
        if image:
            # 极少数情况下，水频（全频词云目标频）不会出子频词云，加个判断去掉 おまけに
            bonus_msg = "おまけに" if int(overall_target_channel) in channels else ""
            msg = MessageSegment.text(
                f"{bonus_msg}💎ヤシマ作戦指揮部💎のフルワードクラウドがこちらです、{Atri.general_word('proud')}"
            ) + MessageSegment.image(image)
            await send_msgs(overall_target_channel, msg)
        else:
            logger.error("全频道词云图片未生成")
            raise Exception("词云图片未生成")
    except Exception as ex:
        # 通常都是签名服务器错误造成的，notice很大可能也发不出去
        notice = f"{Atri.general_word('error')}"
        await send_msgs(debug_channel, notice)
        logger.error(f"生成词云异常：{ex}")
