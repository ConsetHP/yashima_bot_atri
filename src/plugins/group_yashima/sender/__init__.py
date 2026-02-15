from .model import TargetQQGroup as TargetQQGroup
from .model import TargetQQGuildOB11 as TargetQQGuildOB11
from .model import TargetQQGuildOfficial as TargetQQGuildOfficial
from .send import send_msgs as send_msgs
from .adapters import onebot_v11 as onebot_v11, qq as qq


__all__ = ["TargetQQGroup", "TargetQQGuildOB11", "TargetQQGuildOfficial", "send_msgs"]
