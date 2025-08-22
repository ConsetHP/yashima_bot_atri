from abc import ABC, abstractmethod
from io import BytesIO

from typing import Optional, Dict
from pydantic import BaseModel


class Theme(ABC, BaseModel):
    """theme基类"""

    name: str
    """theme名称"""

    def do_render(self, frequency: Dict[str, float]) -> Optional[BytesIO]:
        """渲染词云图片"""
        wordcloud_options = self.prepare_options()
        return self.render(frequency, wordcloud_options)

    @abstractmethod
    def prepare_options(self) -> dict:
        """加载词云参数"""
        ...

    @abstractmethod
    def render(
        self, frequency: Dict[str, float], wordcloud_options: dict
    ) -> Optional[BytesIO]: ...


class ThemeRegistrationError(Exception):
    """Theme注册错误"""

    pass


class ThemeRenderError(Exception):
    """Theme渲染错误"""

    pass
