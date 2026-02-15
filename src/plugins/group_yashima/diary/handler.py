import json

from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.log import logger

from .database import database


def build_msg_content(data_type: str, data: dict) -> str:
    return json.dumps([{"type": data_type, "data": data}], ensure_ascii=False)


async def save_group_message_handle(event: GroupMessageEvent, bot: Bot):
    """保存群聊消息"""
    if len(event.get_message()) < 1:
        return
    if len(event.get_message()) > 1:
        # 有多个segment时，通常是回复/图文/at/表情混排的消息
        messages: list[dict] = []
        for per_segment in event.get_message():
            messages.append({"type": per_segment.type, "data": per_segment.data})
        content = json.dumps(messages, ensure_ascii=False)
        await database.save_group_message(
            str(event.message_id), content, str(event.user_id), str(event.group_id)
        )
        return
    msg_segment = event.get_message()[0]
    if msg_segment.type != "json":
        # 普通单条消息
        await database.save_group_message(
            str(event.message_id),
            build_msg_content(msg_segment.type, msg_segment.data),
            str(event.user_id),
            str(event.group_id),
        )
        return
    logger.info(f"消息内容：{msg_segment.data}")
    real_data = json.loads(msg_segment.data["data"])
    if real_data["app"] != "com.tencent.multimsg":
        # 普通json消息，通常是小程序卡片
        await database.save_group_message(
            str(event.message_id),
            build_msg_content("json", real_data),
            str(event.user_id),
            str(event.group_id),
        )
        return
    # 合并转发消息，直接存json字符串
    res_id = real_data["meta"]["detail"]["resid"]
    resp = await bot.get_forward_msg(id=res_id)
    logger.info(f"合并转发内容：\n{resp}")
    content = json.dumps([resp], ensure_ascii=False)
    await database.save_group_message(
        str(event.message_id),
        content,
        str(event.user_id),
        str(event.group_id),
    )
