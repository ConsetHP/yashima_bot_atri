from nonebot.plugin import on_fullmatch

from .handler import checkpoint_handler
from .register import register_table as register_table
from .model import BaseModel as BaseModel
from .initialize import init_database as init_database
from ..utils.rules import guild_is_admin_user


# 数据库手动checkpoint
db_checkpoint_matcher = on_fullmatch(
    "更新数据库", handlers=[checkpoint_handler], permission=guild_is_admin_user
)
__all__ = ["register_table", "BaseModel", "init_database"]
