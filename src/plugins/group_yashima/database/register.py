from typing import Type, TypeVar

from .model import BaseModel


T = TypeVar("T", bound=BaseModel)

tables: list[type[BaseModel]] = []


def register_table(cls: Type[T]) -> Type[T]:
    """将表注册到数据库中"""
    if issubclass(cls, BaseModel):
        tables.append(cls)
    return cls
