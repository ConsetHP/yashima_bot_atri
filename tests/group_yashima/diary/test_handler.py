import json

import pytest

from nonebug.app import App
from pytest_mock.plugin import MockerFixture

from tests.group_yashima.utils.events import fake_group_message_event


@pytest.mark.asyncio
async def test_save_with_pure_text(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message

    from src.plugins.group_yashima.diary import msg_record
    from src.plugins.group_yashima.diary.handler import save_group_message_handle

    event = fake_group_message_event(
        message_id=12340987,
        message=Message("第一条消息"),
        user_id=8888,
        group_id=2233,
    )
    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocked = mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )

        # nonebug环境中的matcher不会主动调用注册至matcher的handler
        await save_group_message_handle(event, bot)  # type: ignore

        mocked.assert_awaited_with(
            "12340987",
            json.dumps(
                [{"type": "text", "data": {"text": "第一条消息"}}], ensure_ascii=False
            ),
            "8888",
            "2233",
        )


@pytest.mark.asyncio
async def test_save_with_single_image(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    from src.plugins.group_yashima.diary import msg_record
    from src.plugins.group_yashima.diary.handler import save_group_message_handle

    event = fake_group_message_event(
        message=Message(MessageSegment.image("123")),
        message_id=12340987,
        user_id=8888,
        group_id=2233,
    )

    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocked = mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )

        await save_group_message_handle(event, bot)  # type: ignore

        image = [
            {
                "type": "image",
                "data": {
                    "file": "123",
                    "type": None,
                    "cache": "true",
                    "proxy": "true",
                    "timeout": None,
                },
            }
        ]

        mocked.assert_awaited_with(
            "12340987",
            json.dumps(
                image,
                ensure_ascii=False,
            ),
            "8888",
            "2233",
        )


@pytest.mark.asyncio
async def test_save_with_multiple_images(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    from src.plugins.group_yashima.diary import msg_record
    from src.plugins.group_yashima.diary.handler import save_group_message_handle

    event = fake_group_message_event(
        message=Message(MessageSegment.image("123") + MessageSegment.image("234")),
        message_id=12340987,
        user_id=8888,
        group_id=2233,
    )

    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocked = mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )

        await save_group_message_handle(event, bot)  # type: ignore

        images = [
            {
                "type": "image",
                "data": {
                    "file": "123",
                    "type": None,
                    "cache": "true",
                    "proxy": "true",
                    "timeout": None,
                },
            },
            {
                "type": "image",
                "data": {
                    "file": "234",
                    "type": None,
                    "cache": "true",
                    "proxy": "true",
                    "timeout": None,
                },
            },
        ]

        mocked.assert_awaited_with(
            "12340987",
            json.dumps(
                images,
                ensure_ascii=False,
            ),
            "8888",
            "2233",
        )


@pytest.mark.asyncio
async def test_save_with_mixed_messages(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    from src.plugins.group_yashima.diary import msg_record
    from src.plugins.group_yashima.diary.handler import save_group_message_handle

    event = fake_group_message_event(
        message=Message(
            MessageSegment.at(233)
            + MessageSegment.text("123")
            + MessageSegment.face(10)
            + MessageSegment.image("234"),
        ),
        message_id=12340987,
        user_id=8888,
        group_id=2233,
    )

    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocked = mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )

        await save_group_message_handle(event, bot)  # type: ignore

        msgs = [
            {"type": "at", "data": {"qq": "233"}},
            {"type": "text", "data": {"text": "123"}},
            {"type": "face", "data": {"id": "10"}},
            {
                "type": "image",
                "data": {
                    "file": "234",
                    "type": None,
                    "cache": "true",
                    "proxy": "true",
                    "timeout": None,
                },
            },
        ]

        mocked.assert_awaited_with(
            "12340987",
            json.dumps(
                msgs,
                ensure_ascii=False,
            ),
            "8888",
            "2233",
        )


@pytest.mark.asyncio
async def test_save_with_miniapp_card(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    from src.plugins.group_yashima.diary import msg_record
    from src.plugins.group_yashima.diary.handler import save_group_message_handle

    mini_app = {
        "config": {
            "height": 0,
            "forward": 1,
            "ctime": 1768300498,
            "width": 0,
            "type": "normal",
            "token": "ee3776cede931a8077bfac2574b6036f",
            "autoSize": 0,
        },
        "prompt": "[QQ小程序]我推的孩子第三季 OP「TEST ME」by ちゃんみな",
        "app": "com.tencent.miniapp_01",
        "ver": "0.0.0.1",
        "appID": "100951776",
        "view": "view_8C8E89B49BE609866298ADDFF2DBABA4",
        "meta": {
            "detail_1": {
                "appid": "1109937557",
                "preview": "https://pic.ugcimg.cn/cd3144f6ccbb2fd4ffff63f702c2c2ff/jpg1",
                "shareTemplateData": {},
                "gamePointsUrl": "",
                "gamePoints": "",
                "url": "m.q.qq.com/a/s/9465148fa615528e0ceceb74a9803c25",
                "appType": 0,
                "desc": "我推的孩子第三季 OP「TEST ME」by ちゃんみな",
                "title": "哔哩哔哩",
                "scene": 1036,
                "host": {"uin": 1234, "nick": "喵喵喵"},
                "icon": "https://open.gtimg.cn/open/app_icon/00/95/17/76/100951776_100_m.png?t=1767859525",
                "shareTemplateId": "8C8E89B49BE609866298ADDFF2DBABA4",
                "qqdocurl": "https://b23.tv/ulsXGh9",
                "showLittleTail": "",
                "shareOrigin": 0,
            }
        },
        "bthirdappforward": True,
        "bthirdappforwardforbackendswitch": True,
        "desc": "",
    }
    mini_app_seg = MessageSegment.json(json.dumps(mini_app, ensure_ascii=False))
    event = fake_group_message_event(
        message_id=12340987,
        message=Message(mini_app_seg),
        user_id=8888,
        group_id=2233,
    )
    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocked = mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )
        await save_group_message_handle(event, bot)  # type: ignore
        msg = [{"type": "json", "data": mini_app}]
        mocked.assert_awaited_with(
            "12340987",
            json.dumps(
                msg,
                ensure_ascii=False,
            ),
            "8888",
            "2233",
        )


@pytest.mark.asyncio
async def test_save_with_multimsg(app: App, mocker: MockerFixture):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    from src.plugins.group_yashima.diary import msg_record
    from src.plugins.group_yashima.diary.handler import save_group_message_handle

    # 合并转发消息的event都是不完整的summary，调用/get_forward_msg后获取的才是真正的合并转发
    simple_multimsg = {
        "meta": {"detail": {"resid": "1234"}},
        "app": "com.tencent.multimsg",
    }
    simple_multimsg_seg = MessageSegment.json(json.dumps(simple_multimsg))
    event = fake_group_message_event(
        message_id=12340987,
        message=Message(simple_multimsg_seg),
        user_id=8888,
        group_id=2233,
    )
    real_multimsg = {
        "messages": [
            {
                "content": "Meow Meow",
                "group_id": 114514,
                "sender": {"nickname": "喵", "user_id": 2333},
                "time": 1768050256,
            },
            {
                "content": "にゃんにゃん",
                "group_id": 114514,
                "sender": {"nickname": "cat", "user_id": 3322},
                "time": 1768050266,
            },
        ]
    }
    async with app.test_matcher(msg_record) as ctx:
        bot = ctx.create_bot()
        mocked_save = mocker.patch(
            "src.plugins.group_yashima.diary.handler.database.save_group_message",
            new_callable=mocker.AsyncMock,
        )
        ctx.receive_event(bot, event)
        # should_call_api mock掉了bot.api_call，不需要自己写mock
        ctx.should_call_api("get_forward_msg", {"id": "1234"}, real_multimsg)

        await save_group_message_handle(event, bot)  # type: ignore
        mocked_save.assert_awaited_with(
            "12340987",
            json.dumps(
                [real_multimsg],
                ensure_ascii=False,
            ),
            "8888",
            "2233",
        )
