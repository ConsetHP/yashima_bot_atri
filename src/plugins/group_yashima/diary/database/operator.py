import json

from datetime import datetime
from typing import Optional

from nonebot.log import logger

from .model import QQUser, GroupUser, Group, GroupMessage
from ...database.model import db
from ...exceptions import GroupNotJoinedException
from ...utils import get_group_member_info, get_group_info


class DBOperator:
    @db.atomic()
    async def save_group_message(
        self, message_id: str, content: str, user_id: str, group_id: str
    ):
        """保存群聊消息"""
        # TODO: 增加更新过期用户、群聊信息的逻辑
        user_query = self.query_qq_user_by_id(user_id)
        if not user_query:
            member_info = await get_group_member_info(
                group_id=group_id, user_id=user_id
            )
            user_query = QQUser.create(
                user_id=user_id,
                nickname=member_info["nickname"],
                sex=member_info["sex"],
                age=member_info["age"],
            )
        group_user_query = self.query_group_user_by_id(
            group_id=group_id, user_query=user_query
        )
        if not group_user_query:
            member_info = await get_group_member_info(
                group_id=group_id, user_id=user_id
            )
            if not group_id == str(member_info["group_id"]):
                logger.warning(
                    "事件group_id与接口返回group_id不同，这不该发生，请检查go-cqhttp源码!"
                )
            known_keys = [
                "group_id",
                "user_id",
                "nickname",
                "card",
                "sex",
                "age",
                "join_time",
                "last_sent_time",
            ]
            extra_data = {
                key: val for key, val in member_info.items() if key not in known_keys
            }
            group_user_query = GroupUser.create(
                group_id=group_id,
                user=user_query,
                nickname=member_info["card"],
                joined_time=datetime.fromtimestamp(member_info["join_time"]),
                last_sent_time=datetime.fromtimestamp(member_info["last_sent_time"]),
                extra_data=json.dumps(extra_data),
            )
        group_query = self.query_group_by_id(group_id=group_id)
        if not group_query:
            group_info = await get_group_info(group_id=group_id)
            if (
                group_info["group_create_time"] == 0
                and group_info["member_count"] == 0
                and group_info["max_member_count"] == 0
            ):
                logger.warning(f"机器人未入群，group_info：{group_info}")
                raise GroupNotJoinedException
            if not group_id == str(group_info["group_id"]):
                logger.warning(
                    "事件group_id与接口返回group_id不同，这不该发生，请检查go-cqhttp源码!"
                )
            known_keys = ["group_id", "group_name", "group_create_time"]
            extra_data = {
                key: val for key, val in group_info.items() if key not in known_keys
            }
            group_query = Group.create(
                group_id=group_id,
                group_name=group_info["group_name"],
                group_create_time=group_info["group_create_time"],
                extra_data=extra_data,
            )
        GroupMessage.create(
            message_id=message_id,
            content=content,
            user=group_user_query,
            group=group_query,
        )

    def query_qq_user_by_id(self, user_id: str) -> Optional[QQUser]:
        query: Optional[QQUser] = QQUser.get_or_none(QQUser.user_id == user_id)
        return query

    def query_group_user_by_id(
        self, group_id: str, user_query: QQUser
    ) -> Optional[GroupUser]:
        query: Optional[GroupUser] = GroupUser.get_or_none(
            (GroupUser.group_id == group_id) & (GroupUser.user == user_query)
        )
        return query

    def query_group_by_id(self, group_id: str) -> Optional[Group]:
        query: Optional[Group] = Group.get_or_none(Group.group_id == group_id)
        return query

    def clear_db(self):
        """清空数据库，测试用"""
        Group.delete().execute()
        GroupUser.delete().execute()
        GroupMessage.delete().execute()
        QQUser.delete().execute()


database = DBOperator()
