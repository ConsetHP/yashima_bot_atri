from .builder import ReportBuilder


class ReportManager:
    def __init__(self):
        self.builder = ReportBuilder()

    def build_report_data(self):
        self.builder.build_active_period_banner()
        self.builder.build_active_user_count_banner()
        self.builder.build_week_bar_plot()
        self.builder.build_day_bar_plot()

    def get_report(self):
        return self.builder.get_report()
