from nonebot.adapters.qq import MessageCreateEvent
from nonebot.adapters.qq import Bot

from .database.operator import save_guild_message


async def save_received_guild_msg_handle(event: MessageCreateEvent, bot: Bot):
    """保存接收到的频道消息"""
    msg_text = event.get_plaintext()
    image_urls: list[str] = []
    for msg_segment in event.get_message():
        if msg_segment.type in ["image", "attachment"]:
            url = (
                msg_segment.data["url"]
                if msg_segment.data["url"].startswith("http")
                else f"https://{msg_segment.data['url']}"
            )
            image_urls.append(url)

    user_id = event.get_user_id()
    guild_user = await bot.get_member(guild_id=event.guild_id, user_id=user_id)
    guild_roles = (
        await bot.get_guild_roles(guild_id=event.guild_id)
    ).roles  # 频道所有的身份组详情
    user_roles = [
        per_guild_role
        for per_guild_role in guild_roles
        if per_guild_role.id in guild_user.roles
    ]  # 用户所属的身分组列表详情
    channel = await bot.get_channel(channel_id=event.channel_id)

    if msg_text == "":
        msg_text = None
    if len(image_urls) == 0:
        image_urls = None

    save_guild_message(
        channel=channel,
        guild_user=guild_user,
        user_roles=user_roles,
        message_id=event.id,
        text=msg_text,
        images=image_urls,
    )
