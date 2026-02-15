from datetime import datetime, timedelta
from pytest_mock.plugin import MockerFixture

from nonebug.app import App
from time_machine import TimeMachineFixture

from tests.group_yashima.utils.patches import (
    save_fake_message,
)


async def test_get_group_message_between(
    app: App, time_machine: TimeMachineFixture, mocker: MockerFixture
):
    from src.plugins.group_yashima.report.database import (
        database as analyzer_operator,
    )

    today = datetime.now().replace(hour=12)
    yesterday = today - timedelta(days=1)

    time_machine.move_to(yesterday, tick=False)
    await save_fake_message(987, 123, "haha", mocker)

    time_machine.move_to(today, tick=False)
    await save_fake_message(987, 456, "hello", mocker)

    today_messages = analyzer_operator.get_group_message_between(
        today.replace(hour=0, minute=0, second=0),
        today.replace(hour=23, minute=59, second=59),
    )

    assert len(today_messages) == 1
    assert today_messages[0].content == "hello"

    yesterday_messages = analyzer_operator.get_group_message_between(
        yesterday.replace(hour=0, minute=0, second=0),
        yesterday.replace(hour=23, minute=59, second=59),
    )

    assert len(yesterday_messages) == 1
    assert yesterday_messages[0].content == "haha"


async def test_get_active_group_user_between(
    app: App, time_machine: TimeMachineFixture, mocker: MockerFixture
):
    from src.plugins.group_yashima.report.database import (
        database as analyzer_operator,
    )

    today = datetime.now().replace(hour=12)
    yesterday = today - timedelta(days=1)

    time_machine.move_to(yesterday, tick=False)
    await save_fake_message(987, 123, "from yesterday", mocker)

    await save_fake_message(567, 123, "from another group", mocker)

    await save_fake_message(567, 234, "from another group too", mocker)

    await save_fake_message(987, 234, "same group but yesterday", mocker)

    time_machine.move_to(today, tick=False)
    await save_fake_message(987, 234, "same group but today", mocker)

    await save_fake_message(987, 234, "another from same user", mocker)

    today_users = analyzer_operator.get_active_group_user_between(
        today.replace(hour=0, minute=0, second=0),
        today.replace(hour=23, minute=59, second=59),
        group_id="987",
    )

    assert today_users.count() == 1
    assert today_users[0].nickname == "card_234"

    yesterday_users = analyzer_operator.get_active_group_user_between(
        yesterday.replace(hour=0, minute=0, second=0),
        yesterday.replace(hour=23, minute=59, second=59),
        group_id="567",
    )

    assert yesterday_users.count() == 2
    user_names = [per_user.nickname for per_user in yesterday_users]
    assert "card_123" in user_names
    assert "card_234" in user_names

    no_user = analyzer_operator.get_active_group_user_between(
        today.replace(hour=0, minute=0, second=0),
        today.replace(hour=23, minute=59, second=59),
        group_id="567",
    )

    assert no_user.count() == 0


async def test_get_grouped_message_counts_by_time(
    app: App, time_machine: TimeMachineFixture, mocker: MockerFixture
):
    from src.plugins.group_yashima.report.database import (
        database as analyzer_operator,
    )

    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59)
    time_machine.move_to(today_start, tick=False)
    msg_count_per_hour = [0] * 24
    msg_count_per_hour[0] = 1
    msg_count_per_hour[3] = 5
    msg_count_per_hour[7] = 9
    test_msg_counts = [("00", 1), ("03", 5), ("07", 9)]  # [(hour, count)]
    for msg_count in msg_count_per_hour:
        if msg_count == 0:
            time_machine.shift(timedelta(hours=1))
            continue
        for _ in range(msg_count):
            await save_fake_message(987, 123, "hello", mocker)
        time_machine.shift(timedelta(hours=1))
    query = analyzer_operator.get_grouped_message_counts_by_time(today_start, today_end)
    actual_msg_counts = [(msg_group.hour, msg_group.count) for msg_group in query]
    assert len(test_msg_counts) == len(actual_msg_counts)
    assert test_msg_counts == actual_msg_counts


async def test_get_grouped_message_content_by_time(
    app: App, time_machine: TimeMachineFixture, mocker: MockerFixture
):
    from src.plugins.group_yashima.report.database import (
        database as analyzer_operator,
    )

    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59)
    time_machine.move_to(today_start, tick=False)
    msg_count_per_hour = [0] * 24
    msg_count_per_hour[0] = 1
    msg_count_per_hour[3] = 2
    test_msg_contents = [
        ("00", "hello_0"),
        ("03", "hello_0"),
        ("03", "hello_1"),
    ]  # [(hour, content)]
    for msg_count in msg_count_per_hour:
        if msg_count == 0:
            time_machine.shift(timedelta(hours=1))
            continue
        for i in range(msg_count):
            await save_fake_message(987, 123, f"hello_{i}", mocker)
        time_machine.shift(timedelta(hours=1))
    query = analyzer_operator.get_labeled_message_content_by_time(
        today_start, today_end
    )
    actual_msg_content = [(per_msg.hour, per_msg.content) for per_msg in query]
    assert len(test_msg_contents) == len(actual_msg_content)
    assert test_msg_contents == actual_msg_content
