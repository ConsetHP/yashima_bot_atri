from typing import ClassVar

from nonebot import logger

from .types import Theme, ThemeRegistrationError
from ...utils import get_config


class ThemeManager:
    __themes: ClassVar[dict[str, Theme]] = {}

    def register(self, theme: Theme):
        logger.trace(f"登记主题中: {theme}")
        if theme.name in self.__themes:
            raise ThemeRegistrationError(f"主题： {theme.name} 已登记")
        if theme.need_browser and not get_config()["subscribe"]["browser_render_theme"]:
            logger.opt(colors=True).warning(
                f"主题 <b><u>{theme.name}</u></b> 需要浏览器渲染, 但是设置未启用"
            )
        self.__themes[theme.name] = theme
        logger.opt(colors=True).success(f"Theme <b><u>{theme.name}</u></b> registered")

    def unregister(self, theme_name: str):
        logger.trace(f"取消登记主题中: {theme_name}")
        if theme_name not in self.__themes:
            raise ThemeRegistrationError(f"主题 {theme_name} 未被取消登记")
        self.__themes.pop(theme_name)
        logger.opt(colors=True).success(f"主题 <b><u>{theme_name}</u></b> 已取消登记")

    def __getitem__(self, theme: str):
        return self.__themes[theme]

    def __len__(self):
        return len(self.__themes)

    def __contains__(self, theme: str):
        return theme in self.__themes


theme_manager = ThemeManager()
