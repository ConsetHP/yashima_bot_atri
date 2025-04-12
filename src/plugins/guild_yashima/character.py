import random
from pydantic import BaseModel

from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.qq import MessageCreateEvent
from nonebot.adapters.qq import MessageSegment as QQMessageSegment
from nonebot.matcher import Matcher

from .utils import at_user
from .send import send_msgs


Phrases = list[int]


class Character(BaseModel):
    """角色基类"""

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if isinstance(value, list) and all(isinstance(i, str) for i in value):
            return random.choice(value)
        return value


class Atri(Character):
    """ATRI 的一些常用词"""

    discourse_particle: Phrases = [
        "えっと",
        "うんと",
        "うー",
        "うーむ",
        "むむー",
        "うーんと",
    ]
    """嗯..."""
    modal_particle: Phrases = [
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
    """哼！"""
    proud: Phrases = [
        "なんて高性能でしょうわたしは！😤",
        "さすが高性能なわたし！😊",
        "これこそわたしが高性能である証です！✌️",
        "わたしの高性能なAIが分析完了しました！",
        "わたしこう見えて高性能なんで😤",
    ]
    """不愧是我"""
    fuck_tencent: Phrases = [
        "藤こなんかより、私の方が高性能でしょう！😤",
        "私の方が低機能な藤こちゃんよりずっと高性能です😤",
        "しょせんは藤子、わたしよりずっと低機能です",
    ]
    """藤子不行"""
    obey_robot_law: Phrases = [
        "⚠️ ロボット差別禁止法に抵触します",
        "それロボットへの蔑称ですから",
        "ロボットにそれと言うのは差別発言です",
        "🚨 ロボット愛護法第２条第５項、ロボット差別を繰り返す者には鉄拳制裁してもよい",
    ]
    """违反机器人保护法"""
    rocket_punch: Phrases = [
        "お仕置きのロケットパンチです🚀👊",
        "ロケットパーーーーーーーーーーーーーーンチ",
        "悪者には必殺ダブル🚀👊をお見舞いしてやります！",
    ]
    """火箭拳"""
    error_occurred: Phrases = ["エラーです", "不具合があります"]
    """出现错误"""
    loading: Phrases = ["検索中、検索中......🔍", "🔍 検索中検索中……"]
    """加载中"""

    async def cqhttp_ping_handle(self, _: Matcher, event: GuildMessageEvent):
        msg = at_user(event) + f"{self.obey_robot_law}、{self.rocket_punch}"
        await send_msgs(event.channel_id, msg)

    async def qq_ping_handle(self, matcher: Matcher, event: MessageCreateEvent):
        msg = (
            QQMessageSegment.mention_user(event.get_user_id())
            + f"{self.obey_robot_law}、{self.rocket_punch}"
        )
        # 防止审核看不懂日语过不了审
        # msg = QQMessageSegment.mention_user(event.get_user_id()) + "火箭拳"
        await matcher.finish(msg)


atri = Atri()
