from nonebot.matcher import Matcher
from nonebot_plugin_guild_patch import GuildMessageEvent

from ...utils import get_config
from ...send import send_msgs


async def clock_help_handle(_: Matcher, event: GuildMessageEvent):
    msg = f"""しばらく中国語モードにスウィッチします、なにせ高性能ですから！
自习打卡相关指令。每次自习最长时间为{get_config()["guild"]["clock_overtime"]}分钟，超时未结束将自动签退，需修正时间后才能开始新的自习。
@bot 自习帮助
@bot 开始自习
@bot 结束自习
@bot 我的自习   （查询自己的自习统计数据）
@bot /自习修正 3小时30分（或者'2小时'、'45分'等，时长也不能超过上述最长时间，注意开头斜杠）
@bot 破铜烂铁   （抖M福利）"""
    await send_msgs(event.channel_id, msg)
