from pathlib import Path
from typing import TYPE_CHECKING

from .utils import template_to_pic

if TYPE_CHECKING:
    from src.plugins.group_yashima.report import ReportData


class Renderer:
    template_path: Path = Path(__file__).parent / "templates"
    template_name: str = "report.html.jinja"

    def __init__(self, template_data: "ReportData"):
        self.template_data = template_data

    async def render(self) -> bytes:
        try:
            image = await template_to_pic(
                template_path=self.template_path.as_posix(),
                template_name=self.template_name,
                templates={
                    "data": self.template_data,
                },
                pages={
                    "viewport": {"width": 430, "height": 932},
                },
                wait=10,
            )
        except Exception as ex:
            raise Exception(f"渲染文本失败: {ex}")
        else:
            return image
