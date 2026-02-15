import nonebot_plugin_guild_patch  # noqa: F401

from . import report, config, database, diary, notice, sender
from .database import init_database
from .config import get_config


init_database(get_config().db.file_name)


__all__ = ["report", "config", "database", "diary", "notice", "sender"]
