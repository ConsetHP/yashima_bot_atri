import pytest

from nonebug.app import App
from pytest_mock.plugin import MockerFixture

from tests.group_yashima.utils.events import fake_group_message_event


@pytest.mark.asyncio
async def test_save_group_message_matcher(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message

    from src.plugins.group_yashima.diary import msg_record

    event = fake_group_message_event(
        message_id=12340987,
        message=Message("测试响应"),
        user_id=8888,
        group_id=2233,
    )
    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission()
        ctx.should_pass_rule()
