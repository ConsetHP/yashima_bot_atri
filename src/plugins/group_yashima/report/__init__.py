from nonebot.plugin import on_fullmatch

from .handler import send_report
from .builder.model import ReportData
from src.plugins.group_yashima.utils import guild_is_admin_user

report = on_fullmatch("每日报告", handlers=[send_report], rule=guild_is_admin_user)

__all__ = ["ReportData"]
