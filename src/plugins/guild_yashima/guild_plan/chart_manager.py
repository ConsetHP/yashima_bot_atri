import seaborn as sns
import matplotlib.pyplot as plt
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import ArgPlainText, CommandArg
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot_plugin_htmlrender import text_to_pic

from .utils import get_chat_channels, save_figure_to_bytes
from .analyzer import get_seniority_dataframe


def compare_seniority_on_channels(compare_seniority: type[Matcher]):
    """对比不同子频道下的用户的入频天数"""

    @compare_seniority.handle()
    async def prepare_get_channels(
        matcher: Matcher,
        _: GuildMessageEvent,
        state: T_State,
        args: Message = CommandArg(),
    ):
        if args.extract_plain_text():
            matcher.set_arg("channel_indexes", args)
        channels: dict[str, str | int | list] = await get_chat_channels()
        sorted_channels = sorted(
            channels,
            key=lambda x: x["channel_name"].encode("gbk", "ignore"),
        )
        res_text = "聊天子频道列表：\n"
        channel_id_idx = {}
        for idx, per_channel in enumerate(sorted_channels, 1):
            channel_id_idx[idx] = per_channel["channel_id"]

            res_text += f"{idx}. {per_channel['channel_name']}\n"
        if not args.extract_plain_text():
            if len(res_text) > 300:
                image = await text_to_pic(res_text)
                await compare_seniority.send(MessageSegment.image(image))
            else:
                await compare_seniority.send(res_text)
        state["channel_id_idx"] = channel_id_idx

    @compare_seniority.got("channel_indexes", "请输入左侧序号，以空格分隔")
    async def get_channels(
        state: T_State, _: GuildMessageEvent, channel_indexes: str = ArgPlainText()
    ):
        channel_id_idx: dict[int, int] = state["channel_id_idx"]  # {idx: channel_id}
        assert channel_id_idx
        channel_id_list = []
        for channel_idx in channel_indexes.split():
            idx = int(channel_idx)
            if idx not in channel_id_idx.keys():
                await compare_seniority.reject("请输入正确序号")
            channel_id = channel_id_idx[idx]
            channel_id_list.append(channel_id)
        state["channel_id_list"] = channel_id_list

    @compare_seniority.handle()
    async def send_gragh(state: T_State):
        channel_ids = state["channel_id_list"]
        try:
            await compare_seniority.send("爬取数据中，请稍等...")
            data = await get_seniority_dataframe(channel_ids)
            sns.set_style("whitegrid", {"font.sans-serif": ["PingFang SC", "Regular"]})
            gragh = sns.histplot(
                data=data,
                y="channel_name",
                stat="count",
                multiple="stack",
                hue="seniority",
                hue_order=["supreme", "master", "pro", "senior", "junior", "noob"],
                palette="mako",
                alpha=1,
            )
            fig = gragh.get_figure()
            fig.tight_layout()
            img = save_figure_to_bytes(fig)
            plt.close(fig)
            await compare_seniority.finish(MessageSegment.image(img))
        except FinishedException as _:
            return
        except Exception as ex:
            logger.warning(f"生成图表错误：{ex}")
            await compare_seniority.finish("图表生成失败")
