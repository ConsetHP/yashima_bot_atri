from peewee import SqliteDatabase

from .base import db
from ..diary.db_model import GuildImgRecord, GuildMessageRecord
from ..subscribe.database.model import (
    GuildSubscribedChannel,
    SubscribeTarget,
    Subscribe,
)
from ..clock.db_model import ClockEventLog


def init_database(db_path: str):
    # logger = logging.getLogger('peewee')
    # logger.addHandler(logging.StreamHandler())
    # logger.setLevel(logging.DEBUG)

    global db
    _db = SqliteDatabase(
        db_path,
        pragmas={
            "foreign_keys": 1,
            "journal_mode": "wal",
            "cache_size": -1 * 4000,  # 4MB
            "ignore_check_constraints": 0,
            "synchronous": 0,
        },
    )
    db.initialize(_db)
    _db.connect()
    _db.create_tables(
        [
            ClockEventLog,
            GuildMessageRecord,
            GuildImgRecord,
            GuildSubscribedChannel,
            SubscribeTarget,
            Subscribe,
        ]
    )
