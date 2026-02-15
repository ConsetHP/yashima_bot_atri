from pytest_mock.plugin import MockerFixture
from nonebug.app import App
from tests.group_yashima.utils.patches import (
    save_fake_message,
)


async def test_save_group_message(app: App, mocker: MockerFixture):
    from src.plugins.group_yashima.diary.database.model import (
        QQUser,
        GroupUser,
        Group,
        GroupMessage,
    )

    await save_fake_message(987, 123, "hello", mocker)

    await save_fake_message(876, 234, "hi", mocker)

    query = (
        GroupMessage.select(GroupMessage, Group)
        .join(Group, on=(GroupMessage.group == Group.id))
        .where(Group.group_id == "987")
    )
    assert len(query) == 1
    assert query[0].content == "hello"

    related_group = Group.select().where(Group.group_id == "987")
    related_qq_user = QQUser.select().where(QQUser.user_id == "123")
    related_group_user = GroupUser.select().join(QQUser).where(QQUser.user_id == "123")
    assert len(related_group) == 1
    assert len(related_qq_user) == 1
    assert len(related_group_user) == 1
    assert related_group[0].group_name == "test name_987"
    assert related_qq_user[0].nickname == "haha_123"
    assert related_group_user[0].group_id == "987"
    assert related_group_user[0].nickname == "card_123"
