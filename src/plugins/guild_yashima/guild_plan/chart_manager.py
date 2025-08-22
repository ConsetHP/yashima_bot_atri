import seaborn as sns
import matplotlib.pyplot as plt
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.params import CommandArg

from .utils import save_figure_to_bytes
from .analyzer import build_user_seniorities_dataframe
from ..diary.database.operator import get_all_channels
from ..send import send_msgs


def compare_seniorities_sorted_by_channels(compare_seniority: type[Matcher]):
    """对比不同子频道下活跃用户的入频天数"""

    @compare_seniority.handle()
    async def _(event: GuildMessageEvent, args: Message = CommandArg()):
        # 无参数则按照子频道分类统计
        if not args.extract_plain_text():
            channel_ids: list[str] = get_all_channels()
            data = build_user_seniorities_dataframe(channel_ids)
        # 有参数则不分类，统计所有用户信息
        else:
            data = build_user_seniorities_dataframe()
        try:
            sns.set_style(
                "whitegrid", {"font.sans-serif": ["Sarasa Gothic SC", "Regular"]}
            )
            gragh = sns.histplot(
                data=data,
                y="channel_name",
                stat="count",
                multiple="stack",
                hue="joined_days",
                hue_order=[
                    "(1000, ∞]",
                    "(600, 1000]",
                    "(300, 600]",
                    "(100, 300]",
                    "(30, 100]",
                    "[0, 30]",
                ],
                palette="rocket_r",
                alpha=1,
            )
            fig = gragh.get_figure()
            fig.tight_layout()
            img = save_figure_to_bytes(fig)
            plt.close(fig)
            await send_msgs(event.channel_id, MessageSegment.image(img))
        except Exception as ex:
            logger.warning(f"生成图表错误：{ex}")
            await send_msgs(event.channel_id, "图表生成失败")
