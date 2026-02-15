from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from ...config import get_config


@dataclass
class BigBanner:
    content: str
    description: str


@dataclass
class BarPlotHead:
    content: str
    description: str
    trend: str


@dataclass
class BarPlotLegend:
    type: str


@dataclass
class BarSegment:
    type: str
    ratio: int

    @classmethod
    def text(cls, value: int):
        return cls("text", value)

    @classmethod
    def image(cls, value: int):
        return cls("image", value)

    @classmethod
    def other(cls, value: int):
        return cls("other", value)

    @classmethod
    def get_bar(cls, text: int, image: int, other: int) -> list["BarSegment"]:
        return [BarSegment.text(text), BarSegment.image(image), BarSegment.other(other)]


@dataclass
class BarContainer:
    time_label: str
    bar: list[BarSegment]
    display_value: bool = False
    """是否展示消息数量"""
    percentage: int = 0
    """与最高消息数量的百分比（模板用）"""

    @property
    def bar_width(self) -> int:
        """消息数量"""
        width = 0
        for per_bar in self.bar:
            width += per_bar.ratio
        return width


@dataclass
class BarPlotBody:
    bar_containers: list[BarContainer]
    legend: list[BarPlotLegend]


@dataclass
class BarPlotFoot:
    content: str
    description: str


@dataclass
class BarPlot:
    head: BarPlotHead
    body: BarPlotBody
    foot: Optional[BarPlotFoot] = None


@dataclass
class ReportTitle:
    title: str
    built_date: str
    built_time: str


@dataclass
class ReportData:
    title: ReportTitle = field(
        default_factory=lambda: ReportTitle(
            title=get_config().analyzer.report_title,
            built_date=datetime.now().strftime(r"%Y-%m-%d"),
            built_time=datetime.now().strftime(r"%H:%M"),
        )
    )
    big_banners: Optional[list[BigBanner]] = None
    bar_plots: Optional[list[BarPlot]] = None
