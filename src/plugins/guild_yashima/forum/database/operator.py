from typing import Union, Optional
from datetime import datetime, timedelta

from peewee import (
    ForeignKeyField,
    IntegrityError,
)
from nonebot.log import logger

from .model import (
    ThreadUser,
    ThreadInfo,
    Thread,
    ThreadNotFoundError,
    UserNotFoundError,
    AddThreadError,
)
from ...database.db_init import db


class DBOperator:
    @db.atomic()
    def record_thread_content(
        self,
        user_id: str,
        channel_id: int,
        request_id: int,
        text: Optional[str] = None,
        notify: Optional[bool] = None,
    ):
        """记录用户和帖子具体信息"""
        request_id = request_id
        db_user: Union[ThreadUser, None] = ThreadUser.get_or_none(
            ThreadUser.user_id == user_id
        )
        if not db_user:
            db_user = ThreadUser.create(user_id=user_id, last_request_id=request_id)
        else:
            db_user.last_request_id = request_id
            db_user.last_request_time = datetime.now()
            db_user.save()
        db_content = ThreadInfo(
            user=db_user,
            source_channel_id=channel_id,
            text=text if text else "",
            notify=notify if notify else True,
            request_id=request_id,
        )
        try:
            db_content.save()
        except IntegrityError as e:
            logger.warning(f"发生错误{e}")

    @db.atomic()
    def add_thread(self, channel_id: int, thread_id: str, title: str):
        """补充帖子信息并将用户与帖子关联"""
        request_id = self.extract_request_id_from_title(title)
        info_query = (
            ThreadInfo.select()
            .where(ThreadInfo.request_id == request_id)
            .order_by(ThreadInfo.recv_time.desc())
            .first()
        )
        user_query = (
            ThreadUser.select()
            .where(ThreadUser.last_request_id == request_id)
            .order_by(ThreadUser.last_request_time.desc())
            .first()
        )
        if info_query and user_query:
            db_thread = Thread(
                title=title,
                thread_id=thread_id,
                thread_channel_id=channel_id,
                info=info_query,
                user=user_query,
            )
            db_thread.save()
        else:
            raise AddThreadError(
                f"关联帖子错误，info：{info_query}，user：{user_query}"
            )

    @db.atomic()
    def del_last_thread(self, user_id: str) -> None:
        """删除用户最后一次发送的帖子"""
        user_query: ThreadUser | None = ThreadUser.get_or_none(
            ThreadUser.user_id == user_id
        )
        if user_query:
            info_query: ThreadInfo = (
                ThreadInfo.select()
                .where(ThreadInfo.user == user_query)
                .order_by(ThreadInfo.recv_time.desc())
                .first()
            )
            if info_query:
                info_query.delete_instance()
                self._del_user_if_no_thread(user_query)
            else:
                raise ThreadNotFoundError(f"无法找到用户：{user_id}的 ThreadInfo 记录")
        else:
            raise UserNotFoundError(f"用户记录：{user_id}不存在")

    @db.atomic()
    def del_thread(self, channel_id: int, thread_id: str) -> None:
        """删除指定帖子"""
        thread_query: Thread | None = self.get_thread(
            channel_id=channel_id, thread_id=thread_id
        )
        if thread_query:
            info = thread_query.info
            user = thread_query.user
            info.delete_instance()
            self._del_user_if_no_thread(user)
        else:
            raise ThreadNotFoundError

    @db.atomic()
    def _del_user_if_no_thread(self, user: ForeignKeyField | ThreadUser) -> None:
        """清理没有帖子的用户"""
        thread_count = Thread.select().where(Thread.user == user).count()
        if thread_count == 0:
            user.delete_instance()

    def get_thread(self, channel_id: int, thread_id: str) -> Optional[Thread]:
        """获取指定帖子"""
        return Thread.get_or_none(
            (Thread.thread_channel_id == channel_id) & (Thread.thread_id == thread_id)
        )

    def get_last_thread(self, user_id: str) -> Thread:
        """获取用户发送的最后一次帖子"""
        user_query: Optional[ThreadUser] = ThreadUser.get_or_none(
            ThreadUser.user_id == user_id
        )
        if user_query:
            thread_query: Optional[Thread] = (
                Thread.select(Thread, ThreadUser, ThreadInfo)
                .join(ThreadUser, on=(Thread.user == ThreadUser.id))
                .where(Thread.user == user_query)
                .switch(ThreadInfo)
                .join(ThreadInfo, on=(Thread.info == ThreadInfo.id))
                .order_by(Thread.info.recv_time.desc())
                .first()
            )
            if thread_query:
                return thread_query
            else:
                raise ThreadNotFoundError(f"无法找到用户：{user_id}的 ThreadInfo 记录")
        else:
            raise UserNotFoundError(f"数据库中没有用户：{user_id}的记录")

    def thread_is_just_sent(self, user_id: str) -> Optional[bool]:
        """用户是否刚刚投稿帖子"""
        query: ThreadUser = ThreadUser.get_or_none(ThreadUser.user_id == user_id)
        if query:
            previous_time: datetime = datetime.now()
            request_time: datetime = query.last_request_time
            time_delta = previous_time - request_time
            return True if time_delta < timedelta(minutes=5) else False
        else:
            raise UserNotFoundError(f"数据库中没有用户：{user_id}的记录")

    # 必须在用户会话的最后获取，否则有概率出现用户与帖子绑定混乱的情况
    def get_request_id(self) -> int:
        """获取当前请求id"""
        query: ThreadUser | None = (
            ThreadUser.select().order_by(ThreadUser.last_request_time.desc()).first()
        )
        if query and (query.last_request_id < 999):
            request_day = query.last_request_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            previous_day = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            time_delta = previous_day - request_day
            return query.last_request_id + 1 if time_delta < timedelta(days=1) else 0
        else:
            return 0

    def extract_request_id_from_title(self, title: str) -> int:
        """从标题提取request_id"""
        return int(title[1:4])

    def clear_db(self):
        """测试用，清除数据库中所有帖子相关记录"""
        Thread.delete().execute()
        ThreadInfo.delete().execute()
        ThreadUser.delete().execute()


database = DBOperator()
