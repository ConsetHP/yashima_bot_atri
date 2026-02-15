from .builder import ReportManager
from .renderer import Renderer


async def get_daily_report() -> bytes:
    manager = ReportManager()
    manager.build_report_data()
    report = manager.get_report()
    renderer = Renderer(report)
    return await renderer.render()
