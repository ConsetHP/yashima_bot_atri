from datetime import datetime, timedelta
from collections import Counter

from .model import (
    ReportData,
    BigBanner,
    BarPlotHead,
    BarContainer,
    BarSegment,
    BarPlotBody,
    BarPlotLegend,
    BarPlotFoot,
    BarPlot,
)
from .analyzer import ReportAnalyzer


class ReportBuilder:
    def __init__(self):
        self.report = ReportData()
        self.analyzer = ReportAnalyzer()

    def get_report(self):
        return self.report

    def build_active_period_banner(self):
        if self.report.big_banners is None:
            self.report.big_banners = []
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        busiest_time = timedelta(hours=self.analyzer.analyze_busiest_time_today())
        active_period_start = (today_start + busiest_time).strftime("%H:%M")
        active_period_end = (today_start + busiest_time + timedelta(hours=1)).strftime(
            "%H:%M"
        )
        active_period = f"{active_period_start} - {active_period_end}"
        self.report.big_banners.append(BigBanner(active_period, "最活跃时段"))

    def build_active_user_count_banner(self):
        if self.report.big_banners is None:
            self.report.big_banners = []
        active_user_count = str(self.analyzer.analyze_active_users_today())
        self.report.big_banners.append(BigBanner(active_user_count, "参与人数"))

    def _get_other_type_counts(self, counter: Counter) -> int:
        total = 0
        for segment_type, count in counter.items():
            if segment_type != "text" or segment_type != "image":
                total += count
        return total

    def _build_week_bar_containers(
        self, this_week_start: datetime
    ) -> list[BarContainer]:
        bar_containers = []
        start = this_week_start
        end = this_week_start + timedelta(days=1)
        for i in range(7):
            message_type_counts = self.analyzer.get_message_type_counts_between(
                start, end
            )
            if message_type_counts[0] is None:
                raise ValueError
            bar_segments = [
                BarSegment.text(message_type_counts[0]["text"]),
                BarSegment.image(message_type_counts[0]["image"]),
                BarSegment.other(self._get_other_type_counts(message_type_counts[0])),
            ]
            bar_containers.append(
                BarContainer(
                    self.analyzer.weekdays_nums_map[i],
                    bar_segments,
                    True,
                )
            )
            start += timedelta(days=1)
            end += timedelta(days=1)
        return bar_containers

    def _build_day_bar_segments(self, today_start: datetime) -> list[BarContainer]:
        message_type_counts = self.analyzer.get_message_type_counts_between(
            today_start, today_start + timedelta(days=1), timedelta(hours=1)
        )
        bar_containers = []

        for i, per_type_count in enumerate(message_type_counts):
            if per_type_count is None:
                empty_bar = BarSegment.get_bar(0, 0, 0)
                bar_containers.append(BarContainer(f"{i:02d}:00", empty_bar))
                continue
            bar = BarSegment.get_bar(
                per_type_count["text"],
                per_type_count["image"],
                self._get_other_type_counts(per_type_count),
            )
            bar_containers.append(BarContainer(f"{i:02d}:00", bar))
        return bar_containers

    def _update_bar_containers(
        self, bar_containers: list[BarContainer]
    ) -> list[BarContainer]:
        max_msg_count = max(
            [per_container.bar_width for per_container in bar_containers]
        )
        final_bar_containers = []
        for per_container in bar_containers:
            if max_msg_count > 0:
                percentage = int((per_container.bar_width / max_msg_count) * 100)
            else:
                percentage = 0
            per_container.percentage += percentage
            final_bar_containers.append(per_container)
        return final_bar_containers

    def build_week_bar_plot(self):
        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_end = datetime.now() + timedelta(days=1)
        this_week_start = today_start - timedelta(days=today_start.weekday())  # Monday
        this_week_end = this_week_start + timedelta(
            days=6, hours=23, minutes=59, seconds=59
        )  # Sunday

        # bar plot head
        this_week_average = self.analyzer.analyze_average_message_in_week(
            this_week_start, today_end
        )
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_end - timedelta(days=7)
        last_week_average = self.analyzer.analyze_average_message_in_week(
            last_week_start, last_week_end
        )
        trend_percentage = self.analyzer.calculate_trend_percentage(
            this_week_average, last_week_average
        )
        trend_icon = self.analyzer.get_trend_icon(trend_percentage, 5)
        plot_head = BarPlotHead(
            f"{str(this_week_average)}条",
            "日均消息数",
            f"{trend_icon} 相较上周浮动 {trend_percentage}%",
        )

        # bar plot body
        raw_bar_containers = self._build_week_bar_containers(this_week_start)
        final_bar_containers = self._update_bar_containers(raw_bar_containers)
        plot_body = BarPlotBody(
            final_bar_containers,
            [BarPlotLegend("text"), BarPlotLegend("image"), BarPlotLegend("other")],
        )

        # bar plot foot
        plot_foot = BarPlotFoot(
            "本周消息总数",
            f"{self.analyzer.get_message_count_between(this_week_start, this_week_end)}条",
        )

        if self.report.bar_plots is None:
            self.report.bar_plots = []
        self.report.bar_plots.append(BarPlot(plot_head, plot_body, plot_foot))

    def build_day_bar_plot(self):

        today_start = datetime.now().replace(hour=0, minute=0, second=0)
        today_end = today_start + timedelta(days=1)

        # bar plot head
        today_message_count = self.analyzer.get_message_count_between(
            today_start, today_end
        )
        yesterday_message_count = self.analyzer.get_message_count_between(
            today_start - timedelta(days=1), today_end - timedelta(days=1)
        )
        trend_percentage = self.analyzer.calculate_trend_percentage(
            int(today_message_count), int(yesterday_message_count)
        )
        trend_icon = self.analyzer.get_trend_icon(trend_percentage, 5)
        plot_head = BarPlotHead(
            f"{self.analyzer.get_message_count_between(today_start, today_end)}条",
            "今日消息总数",
            f"{trend_icon} 相较昨天浮动 {trend_percentage}%",
        )

        # bar plot body
        raw_bar_containers = self._build_day_bar_segments(today_start)
        final_bar_containers = self._update_bar_containers(raw_bar_containers)
        plot_body = BarPlotBody(
            final_bar_containers,
            [BarPlotLegend("text"), BarPlotLegend("image"), BarPlotLegend("other")],
        )

        if self.report.bar_plots is None:
            self.report.bar_plots = []
        self.report.bar_plots.append(BarPlot(plot_head, plot_body))
