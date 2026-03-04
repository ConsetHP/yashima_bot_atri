from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from datetime import datetime

from .builder import ReportManager
from .renderer import Renderer


async def get_daily_report(day_start: Optional["datetime"]) -> bytes:
    manager = ReportManager(day_start)
    manager.build_report_data()
    report = manager.get_report()
    renderer = Renderer(report)
    return await renderer.render()
