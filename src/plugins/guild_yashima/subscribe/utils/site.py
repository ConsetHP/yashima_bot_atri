from abc import ABC, abstractmethod
from typing import Literal

from httpx import AsyncClient

from ..types import Target

from .http import http_client


class ClientManager(ABC):
    @abstractmethod
    async def get_client(self, target: Target | None) -> AsyncClient: ...

    @abstractmethod
    async def get_client_for_static(self) -> AsyncClient: ...

    @abstractmethod
    async def get_query_name_client(self) -> AsyncClient: ...

    @abstractmethod
    async def refresh_client(self): ...


class DefaultClientManager(ClientManager):
    async def get_client(self, target: Target | None) -> AsyncClient:
        return http_client()

    async def get_client_for_static(self) -> AsyncClient:
        return http_client()

    async def get_query_name_client(self) -> AsyncClient:
        return http_client()

    async def refresh_client(self):
        pass


class SkipRequestException(Exception):
    """跳过请求异常，如果需要在选择 Cookie 时跳过此次请求，可以抛出此异常"""

    pass


site_manager: dict[str, type["Site"]] = {}


class SiteMeta(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        return super().__new__(cls, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kwargs):
        if kwargs.get("base"):
            # this is the base class
            cls._key = kwargs.get("key")
        elif not kwargs.get("abstract"):
            # this is the subclass
            if "name" in namespace:
                site_manager[namespace["name"]] = cls
        super().__init__(name, bases, namespace, **kwargs)


class Site(metaclass=SiteMeta):
    schedule_type: Literal["date", "interval", "cron"]
    schedule_setting: dict
    name: str
    client_mgr: type[ClientManager] = DefaultClientManager
    require_browser: bool = False
    registry: list[type["Site"]]

    def __str__(self):
        return f"[{self.name}]-{self.name}-{self.schedule_setting}"


def anonymous_site(
    schedule_type: Literal["date", "interval", "cron"], schedule_setting: dict
) -> type[Site]:
    return type(
        "AnonymousSite",
        (Site,),
        {
            "schedule_type": schedule_type,
            "schedule_setting": schedule_setting,
            "client_mgr": DefaultClientManager,
        },
    )
