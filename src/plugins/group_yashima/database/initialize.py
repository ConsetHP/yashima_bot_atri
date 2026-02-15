from peewee import SqliteDatabase

from .model import db
from .register import tables


def init_database(db_path: str):
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
    _db.create_tables(tables)
