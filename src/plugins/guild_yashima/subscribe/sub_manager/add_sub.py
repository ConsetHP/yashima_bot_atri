import contextlib

from nonebot.adapters import Message, MessageTemplate
from nonebot.matcher import Matcher
from nonebot.params import Arg, ArgPlainText
from nonebot.typing import T_State
from nonebot_plugin_guild_patch import GuildMessageEvent

from ..apis import check_sub_target
from ..database import database
from ..database.operator import SubscribeDupException
from ..platform import Platform, platform_manager, unavailable_paltforms
from ..types import Target

from .utils import common_platform, ensure_channel_id, gen_handle_cancel


def do_add_sub(add_sub: type[Matcher]):
    handle_cancel = gen_handle_cancel(add_sub, "已中止订阅")

    add_sub.handle()(ensure_channel_id(add_sub))

    @add_sub.handle()
    async def init_promote(state: T_State):
        state["_prompt"] = (
            "请输入想要订阅的平台，目前支持，请输入冒号左边的名称：\n"
            + "".join(
                [
                    f"{platform_name}: {platform_manager[platform_name].name}\n"
                    for platform_name in common_platform
                ]
            )
            + "要查看全部平台请输入：“全部”\n中止订阅过程请输入：“取消”"
        )

    @add_sub.got("platform", MessageTemplate("{_prompt}"), [handle_cancel])
    async def parse_platform(state: T_State, platform: str = ArgPlainText()) -> None:
        if platform == "全部":
            message = "全部平台\n" + "\n".join(
                [
                    f"{platform_name}: {platform.name}"
                    for platform_name, platform in platform_manager.items()
                ]
            )
            await add_sub.reject(message)
        elif platform == "取消":
            await add_sub.finish("已中止订阅")
        elif platform in platform_manager:
            if platform in unavailable_paltforms:
                await add_sub.finish(
                    f"无法订阅 {platform}，{unavailable_paltforms[platform]}"
                )
            state["platform"] = platform
        else:
            await add_sub.reject(
                "平台名称输入错误，请重新输入。若想取消订阅请输入“取消”来结束订阅流程"
            )

    @add_sub.handle()
    async def prepare_get_id(matcher: Matcher, state: T_State):
        cur_platform = platform_manager[state["platform"]]
        if cur_platform.has_target:
            state["_prompt"] = (
                cur_platform.parse_target_promot
                if cur_platform.parse_target_promot
                else "请输入要订阅的用户id"
            ) + "\n查询用户id获取方法请回复:“查询”"
        else:
            matcher.set_arg("raw_id", None)  # type: ignore
            state["id"] = "default"
            state["name"] = await check_sub_target(state["platform"], Target(""))

    @add_sub.got("raw_id", MessageTemplate("{_prompt}"), [handle_cancel])
    async def got_id(state: T_State, raw_id: Message = Arg()):
        raw_id_text = raw_id.extract_plain_text()
        try:
            if raw_id_text == "查询":
                msg = "相关平台的uid格式或获取方式:\n"
                url = "randomurl.com(测试，别点)"
                msg += url
                await add_sub.reject(msg)
            platform = platform_manager[state["platform"]]
            with contextlib.suppress(ImportError):
                from nonebot.adapters.onebot.v11 import Message
                from nonebot.adapters.onebot.v11.utils import unescape

                if isinstance(raw_id, Message):
                    raw_id_text = unescape(raw_id_text)
            raw_id_text = await platform.parse_target(raw_id_text)
            name = await check_sub_target(state["platform"], raw_id_text)
            if not name:
                await add_sub.reject(
                    "用户id输入错误，请重新输入。若想取消订阅请输入“取消”来结束订阅流程"
                )
            state["id"] = raw_id_text
            state["name"] = name
        except Platform.ParseTargetException as e:
            await add_sub.reject(
                "不能从你的输入中提取出id，请检查你输入的内容是否符合预期"
                + (f"\n{e.prompt}" if e.prompt else "")
            )
        else:
            await add_sub.send(
                f"即将订阅的用户为:【{state['platform']}】 {state['name']} ({state['id']})\n如有错误，请输入“取消”结束订阅流程"
            )

    @add_sub.handle()
    async def prepare_get_categories(matcher: Matcher, state: T_State):
        if not platform_manager[state["platform"]].categories:
            matcher.set_arg("raw_cats", None)  # type: ignore
            state["cats"] = []
            return
        state["_prompt"] = "请输入要订阅的类别，以空格分隔，支持的类别有：{}".format(
            " ".join(list(platform_manager[state["platform"]].categories.values()))
        )

    @add_sub.got("raw_cats", MessageTemplate("{_prompt}"), [handle_cancel])
    async def parser_cats(state: T_State, raw_cats: Message = Arg()):
        raw_cats_text = raw_cats.extract_plain_text()
        res = []
        if platform_manager[state["platform"]].categories:
            for cat in raw_cats_text.split():
                if cat not in platform_manager[state["platform"]].reverse_category:
                    await add_sub.reject(
                        f"不支持 {cat}，请重新输入。若想取消订阅请输入“取消”来结束订阅流程"
                    )
                res.append(platform_manager[state["platform"]].reverse_category[cat])
        state["cats"] = res

    @add_sub.handle()
    async def prepare_get_tags(matcher: Matcher, state: T_State):
        if not platform_manager[state["platform"]].enable_tag:
            matcher.set_arg("raw_tags", None)  # type: ignore
            state["tags"] = []
            return
        state["_prompt"] = (
            '请输入要订阅/屏蔽的标签(不含#号)\n多个标签请使用空格隔开\n订阅所有标签输入"全部标签"\n具体规则回复"详情"'
        )

    @add_sub.got("raw_tags", MessageTemplate("{_prompt}"), [handle_cancel])
    async def parser_tags(state: T_State, raw_tags: Message = Arg()):
        raw_tags_text = raw_tags.extract_plain_text()
        if raw_tags_text == "详情":
            await add_sub.reject(
                "订阅标签直接输入标签内容\n"
                "屏蔽标签请在标签名称前添加~号\n"
                "详见https://nonebot-bison.netlify.app/usage/#%E5%B9%B3%E5%8F%B0%E8%AE%A2%E9%98%85%E6%A0%87%E7%AD%BE-tag"
            )
        if raw_tags_text in ["全部标签", "全部", "全标签"]:
            state["tags"] = []
        else:
            state["tags"] = raw_tags_text.split()

    @add_sub.handle()
    async def add_sub_process(event: GuildMessageEvent, state: T_State):
        try:
            channel_id = event.channel_id
            await database.add_subscribe(
                channel_id=channel_id,
                target=state["id"],
                target_name=state["name"],
                platform_name=state["platform"],
                cats=state.get("cats", []),
                tags=state.get("tags", []),
            )
        except SubscribeDupException:
            await add_sub.finish(f"订阅用户： {state['name']} 失败: 已存在该订阅")
        except Exception as e:
            await add_sub.finish(f"订阅用户： {state['name']} 失败: {e}")
        await add_sub.finish(f"订阅用户： {state['name']} 成功")
