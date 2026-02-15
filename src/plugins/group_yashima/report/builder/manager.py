from .builder import ReportBuilder

from src.plugins.group_yashima.config import get_config


class ReportManager:
    def __init__(self):
        self.builder = ReportBuilder()

    def build_report_data(self):
        if get_config().analyzer.big_banner:
            self.builder.build_active_period_banner()
            self.builder.build_active_user_count_banner()
        if get_config().analyzer.week_bar_plot:
            self.builder.build_week_bar_plot()
        if get_config().analyzer.day_bar_plot:
            self.builder.build_day_bar_plot()

    def get_report(self):
        return self.builder.get_report()
