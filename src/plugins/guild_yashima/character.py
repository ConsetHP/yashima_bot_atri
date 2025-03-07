import random

from nonebot.log import logger
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.qq import MessageCreateEvent
from nonebot.adapters.qq import MessageSegment as QQMessageSegment
from nonebot.matcher import Matcher

from .utils import at_user
from .send import send_msgs


class Atri:
    @staticmethod
    def general_word(key: str) -> str:
        "アトリ 的通用词"
        words = {}
        # 嗯...
        words["discourse_particle"] = [
            "えっと",
            "うんと",
            "うー",
            "うーむ",
            "むむー",
            "うーんと",
        ]
        # 哼！
        words["modal_particle"] = [
            "フンだ",
            "フンスフンス",
            "ふっふっふ",
            "はあ～",
            "ムフン",
            "ふふ",
            "むふふ",
            "ふっふっふっふ",
            "エッヘン",
            "えへへ",
        ]
        # 不愧是我！
        words["proud"] = [
            "なんて高性能でしょうわたしは！😤",
            "さすが高性能なわたし！😊",
            "これこそわたしが高性能である証です！✌️",
            "わたしの高性能なAIが分析完了しました！",
            "わたしこう見えて高性能なんで😤",
        ]
        words["fuck_tencent"] = [
            "藤こなんかより、私の方が高性能でしょう！😤",
            "私の方が低機能な藤こちゃんよりずっと高性能です😤",
            "しょせんは藤子、わたしよりずっと低機能です",
        ]
        # 机器人法
        words["robot_law"] = [
            "⚠️ロボット差別禁止法に抵触します",
            "それロボットへの蔑称ですから",
            "ロボットにそれと言うのは差別発言です",
            "ロボット愛護法第２条第５項、ロボット差別を繰り返す者には鉄拳制裁してもよい",
        ]
        # 火箭拳
        words["rocket_punch"] = [
            "お仕置きのロケットパンチです🚀👊",
            "ロケットパーーーーーーーーーーーーーーンチ",
        ]
        words["error"] = ["エラーです", "不具合があります"]
        words["loading"] = "検索中、検索中......🔍"

        if key in words:
            if type(words[key]) is list:
                return random.choice(words[key])
            elif type(words[key]) is str:
                return words[key]
            else:
                logger.warning("值不存在，将返回空字符串")
                return ""
        else:
            logger.warning("键不存在，将返回空字符串")
            return ""

    @staticmethod
    async def cqhttp_ping_handle(_: Matcher, event: GuildMessageEvent):
        msg = (
            at_user(event)
            + f"{Atri.general_word('robot_law')}、{Atri.general_word('rocket_punch')}"
        )
        await send_msgs(event.channel_id, msg)

    @staticmethod
    async def qq_ping_handle(matcher: Matcher, event: MessageCreateEvent):
        msg = (
            QQMessageSegment.mention_user(event.get_user_id())
            + f"{Atri.general_word('robot_law')}、{Atri.general_word('rocket_punch')}"
        )
        await matcher.finish(msg)
