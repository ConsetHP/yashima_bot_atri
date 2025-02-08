from typing import ClassVar

from nonebot import logger

from .types import Theme, ThemeRegistrationError


class ThemeManager:
    __themes: ClassVar[dict[str, Theme]] = {}

    def register(self, theme: Theme):
        logger.trace(f"登记主题中: {theme}")
        if theme.name in self.__themes:
            raise ThemeRegistrationError(f"主题： {theme.name} 已登记")
        self.__themes[theme.name] = theme
        logger.opt(colors=True).success(f"Theme <b><u>{theme.name}</u></b> registered")

    def __getitem__(self, theme_name: str):
        return self.__themes[theme_name]


theme_manager = ThemeManager()
