import pytest
import nonebot
import time_machine

from pytest_asyncio import is_async_test

# 导入适配器
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from nonebug import App


# 防止time_machine时区混乱，详见 https://time-machine.readthedocs.io/en/latest/installation.html
time_machine.naive_mode = time_machine.NaiveMode.LOCAL


def pytest_collection_modifyitems(items: list[pytest.Item]):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
async def after_nonebot_init(after_nonebot_init: None):
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)

    # 加载插件
    nonebot.load_from_toml("pyproject.toml")


@pytest.fixture
async def app():
    from src.plugins.group_yashima.database import init_database
    from src.plugins.group_yashima.diary.database import database

    init_database("tmp.db")
    yield App()
    database.clear_db()
