"""掉线重连通知，参考https://github.com/Cypas/nonebot_plugin_disconnect_notice"""

import smtplib
import asyncio
import concurrent.futures
from functools import partial
from datetime import datetime, timedelta
from typing import Callable, Optional
from email.header import Header
from email.utils import formataddr

from nonebot import Bot, get_bots, get_driver, require
from nonebot.log import logger
from nonebot_plugin_guild_patch import GuildMessageEvent

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .utils import get_config  # noqa: E402
from .send import send_msgs  # noqa: E402


driver = get_driver()
connect_start_time = datetime.now()
time_need_reset = False


async def test_disconnect_notice_handle(event: GuildMessageEvent):
    """测试是否可正常发送邮件"""
    logger.info("开始发送测试邮件")
    await send_mail("114514", "114514", test=True)
    await send_msgs(event.channel_id, "已发送通知")


def do_schedule(func: Callable, job_id: str, args: Optional[list] = None) -> None:
    """将任务添加到scheduler中"""
    connection_cooldown_time: float = get_config()["notice"]["cd"]
    running_time = datetime.now() + timedelta(seconds=connection_cooldown_time)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        id=job_id,
        func=func,
        args=args,
        misfire_grace_time=60,
        coalesce=True,
        max_instances=1,
        trigger="date",
        run_date=running_time,
    )


@driver.on_bot_connect
async def connect_handler(bot: Bot):
    """重连时更新连接开始时间"""
    platform_name: str = bot.adapter.get_name()
    bot_id: str = bot.self_id
    job_id = f"update_connnect_time_{platform_name}_{bot_id}"
    do_schedule(cron_update_connect_time, job_id, [platform_name, bot_id])


@driver.on_bot_disconnect
async def disconnect_handler(bot: Bot):
    """掉线时发送邮件通知"""
    platform_name: str = bot.adapter.get_name()
    bot_id: str = bot.self_id
    job_id = f"disconnect_notice_{platform_name}_{bot_id}"
    do_schedule(cron_send_mail, job_id, [platform_name, bot_id])


def cron_update_connect_time(platform_name: str, bot_id: str) -> None:
    """定时任务：更新bot连接开始时间"""
    global time_need_reset
    if time_need_reset:
        logger.info(
            f"适配器【{platform_name}】的账号【{bot_id}】已重连，将更新存活开始时间"
        )
        global connect_start_time
        connect_start_time = datetime.now()
        time_need_reset = False
    else:
        logger.info("不更新存活时间")


async def cron_send_mail(platform_name: str, bot_id: str) -> None:
    """定时任务：发送邮件"""
    bots = get_bots()
    bot = bots.get(bot_id)
    # 重新检查bot是否连接
    if not bot:
        logger.warning(
            f"适配器【{platform_name}】的账号【{bot_id}】已下线。即将进行通知"
        )
        global time_need_reset
        time_need_reset = True
        await send_mail(platform_name=platform_name, bot_id=bot_id)
    else:
        logger.info(f"适配器【{platform_name}】的账号【{bot_id}】已重连。不进行通知")


def build_notice_content(platform_name: str, bot_id: str) -> bytes:
    """生成掉线提醒消息"""
    global connect_start_time
    time_delta = datetime.now() - connect_start_time
    time_survived = f"{time_delta.days}天 {time_delta.seconds // 3600}小时 {(time_delta.seconds % 3600) // 60}分钟"
    msg = f"适配器【{platform_name}】的账号【{bot_id}】已下线。\n存活时间：{time_survived}"
    return msg


def build_rfc_mail(mail_user: str, title: str, content: str) -> bytes:
    """构建符合RFC标准的邮件"""
    msg = (
        f"From: {formataddr(('NoneBot通知', mail_user))}\n"
        f"To: {mail_user}\n"
        f"Subject: {Header(title, 'utf-8').encode()}\n"
        f"MIME-Version: 1.0\n"
        f"Content-Type: text/plain; charset=utf-8\n\n"
        f"{content}"
    )
    return msg.encode("utf-8", errors="replace")


async def send_mail(platform_name: str, bot_id: str, test: bool = False) -> None:
    title = "NoneBot 掉线通知" if not test else "[测试] NoneBot 掉线通知"
    content = (
        build_notice_content(platform_name, bot_id)
        if not test
        else "这是一条bot掉线通知消息，bot并未掉线。"
    )
    # 防止同步函数阻塞主事件循环
    logger.info("开始发送通知邮件")
    loop = asyncio.get_running_loop()
    pfunc = partial(do_send_mail, title, content)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, pfunc)


def do_send_mail(title: str, content: str) -> None:
    """发送邮件通知"""
    mail_user: str = str(
        get_config()["notice"]["user"]
    )  # 不使用str()转换会导致连接smpt时报错，下同，该重构get_config了
    mail_host: str = str(get_config()["notice"]["host"])
    mail_port: int = int(get_config()["notice"]["port"])
    mail_key: str = str(get_config()["notice"]["key"])

    try:
        with smtplib.SMTP_SSL(
            host=mail_host, port=mail_port
        ) as smtp:  # 使用SMTP_SSL需要服务器支持
            smtp.login(mail_user, mail_key)
            smtp.sendmail(
                mail_user, mail_user, build_rfc_mail(mail_user, title, content)
            )
    except smtplib.SMTPResponseException as smtpres:
        if smtpres.smtp_code == -1 and mail_host == "smtp.qq.com":
            # QQ邮箱返回
            logger.info("通知邮件发送成功，但是服务器响应异常，可以无视这条日志")
        else:
            logger.warning(
                f"服务器响应异常：code={smtpres.smtp_code}, msg={smtpres.smtp_error}"
            )
    except Exception as ex:
        logger.warning(f"通知邮件发送失败，未知错误：{ex}")
    else:
        logger.info("通知邮件发送成功")
