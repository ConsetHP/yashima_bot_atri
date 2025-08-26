import re

from dataclasses import dataclass
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

from nonebot.adapters.qq.models import User

from .utils import get_img_size


class ContentEmptyException(Exception):
    """消息内容为空"""


class RawUpload(BaseModel):
    author: User
    """消息的作者"""
    content: "Content"
    """消息内容"""


class Upload(RawUpload):
    """真正投稿到帖子中的upload"""

    info: "UploadInfo"
    """附加信息"""
    title: str = "快速发帖"
    """标题"""
    reply: "Reply | None" = None
    """转发的消息"""

    def is_reply_myself(self) -> bool:
        """用户在使用一键发帖时，是否回复了自己的消息"""
        if not self.reply:
            return True
        return True if self.author.id == self.reply.author.id else False

    async def generate(self) -> str:
        """生成投稿内容（markdown格式）"""
        self._generate_title()
        if self.reply:
            md_content = (
                f"🆔 {self.author.username}\n" if self.is_reply_myself() else ""
            )
        else:
            md_content = f"🆔 {self.author.username}\n"
        md_content += f"🔃 转发自 #{self.info.source_channel.name}\n"
        # 添加分割线
        md_content += "==============\n"
        # 添加文字与图片
        if self.content.text:
            md_content += self.content.text + "\n"
        if self.reply:
            md_content += (
                self.reply.content.text + "\n" if self.reply.content.text else ""
            )
            if reply_images := self.reply.content.images:
                for per_url in reply_images:
                    img_w, img_h = await get_img_size(per_url)
                    md_content += f"![图片 #{img_w}px #{img_h}px]({per_url})\n"
        if img_urls := self.content.images:
            for per_url in img_urls:
                img_w, img_h = await get_img_size(per_url)
                md_content += f"![图片 #{img_w}px #{img_h}px]({per_url})\n"
        print(md_content)

        return md_content

    def _generate_title(self) -> None:
        """根据投稿内容生成帖子标题"""
        image_only_prompt = "分享图片"
        raw_title = ""
        if self.reply:
            if not self.content.text and not self.reply.content.text:
                self.title = image_only_prompt
                return
            elif not self.content.text and self.reply.content.text:
                raw_title = self.reply.content.text
            else:
                raw_title = self.content.text
        else:
            if not self.content.text:
                self.title = image_only_prompt
                return
            else:
                raw_title = self.content.text
        match = re.search(r"^(.*?)\n", raw_title)

        if match:
            text = match.group(1)
            self.title = f"{text[:15]}..." if len(text) > 15 else text
        else:
            text = raw_title
            self.title = f"{text[:15]}..." if len(text) > 15 else text


class Reply(RawUpload): ...


class Content(BaseModel):
    text: str | None = None
    """文本内容"""
    images: list[str] | None = None
    """图片URL"""

    @model_validator(mode="after")
    def validate_not_empty(self):
        if self.text is None and self.images is None:
            raise ValueError("消息内容不可为空")
        return self


class UploadInfo(BaseModel):
    source_channel: "Channel"
    """来源频道"""
    target_channel: "Channel"
    """目标频道"""
    nickname: str | None = None
    """发布者昵称"""
    upload_time: datetime = Field(default_factory=datetime.now)
    """上传时间"""


@dataclass(eq=True, frozen=True)
class Channel:
    id: str
    """频道id"""
    name: str
    """频道名称"""
