from nonebot.matcher import Matcher
from nonebot.adapters.qq import MessageCreateEvent


async def send_help(matcher: Matcher, _: MessageCreateEvent):
    prompt = """✨ /一键发帖

🛠️ 基础用法：
    直接输入 '@bot /一键发帖 <投稿内容>'

📃 参数说明：
    投稿内容：必须，类型可为 文字 或 图文 或 图片。支持 Markdown 部分格式
    ※ 参数之间需用空格间隔

🛠️ 特殊用法：
    - 长按引用想要投稿的消息
    - 删除@被引用人（如果有的话）
    - 保持引用消息状态并输入 '@bot /一键发帖'

✨ /撤回发帖

🛠️ 用法：
    直接输入 '@bot /撤回发帖'，可以撤回最后一次使用'/一键发帖'发送的帖子

✨ /萝卜子

🛠️ 用法：
    直接输入 '@bot /萝卜子'，可以吃到火箭拳
"""
    await matcher.finish(prompt)
