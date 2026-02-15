from uuid import uuid4

from pytest_mock.plugin import MockerFixture


def patch_get_group_member_info(group_id: int, user_id: int, mocker: MockerFixture):
    """避免直接调用适配器接口"""
    fake_member_info = {
        "group_id": group_id,
        "user_id": user_id,
        "nickname": f"haha_{user_id}",
        "card": f"card_{user_id}",
        "sex": "unknown",
        "age": 0,
        "area": "US",
        "join_time": 1769294125,
        "last_sent_time": 1769294154,
        "level": "1",
        "role": "owner",
        "unfriendly": False,
        "title": "test title",
        "title_expire_time": 1769294261,
        "card_changeable": True,
        "shut_up_timestamp": 1769294301,
    }
    mocker.patch(
        "src.plugins.group_yashima.diary.database.operator.get_group_member_info",
        return_value=fake_member_info,
        new_callable=mocker.AsyncMock,
    )


def patch_get_group_info(group_id: int, mocker: MockerFixture):
    """避免直接调用适配器接口"""
    fake_group_info = {
        "group_id": group_id,
        "group_name": f"test name_{group_id}",
        "group_memo": "this is a desc",
        "group_create_time": 1769294995,
        "group_level": 999,
        "member_count": 10,
        "max_member_count": 100,
    }
    mocker.patch(
        "src.plugins.group_yashima.diary.database.operator.get_group_info",
        return_value=fake_group_info,
        new_callable=mocker.AsyncMock,
    )


async def save_fake_message(
    group_id: int, user_id: int, content: str, mocker: MockerFixture
) -> str:
    from src.plugins.group_yashima.diary.database import database

    patch_get_group_member_info(group_id, user_id, mocker)
    patch_get_group_info(group_id, mocker)
    msg_id = str(uuid4())  # 实际msg_id并不是uuid，此处只是方便测试
    await database.save_group_message(msg_id, content, str(user_id), str(group_id))
    return msg_id
