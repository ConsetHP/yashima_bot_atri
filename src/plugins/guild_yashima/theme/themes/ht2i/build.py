import re

from collections.abc import Sequence
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from nonebot.adapters.onebot.v11 import MessageSegment

from ....post.protocol import HTMLContentSupport
from ....theme import Theme, ThemeRenderError
from ....utils import is_pics_mergable, pic_merge

if TYPE_CHECKING:
    from ....post import Post


class Ht2iTheme(Theme):
    """使用浏览器将文本渲染为图片

    HTML render Text To Image.
    需要安装`nonebot_plugin_htmlrender`插件
    """

    name: Literal["ht2i"] = "ht2i"
    need_browser: bool = True

    def _replace_single_newline_with_double(self, text: str) -> str:
        """将单次换行转换成两次换行，避免渲染成图片后单次换行不换行"""
        replaced_text = re.sub(r"(?<!\n)\n(?!\n)", "\n\n", text)
        return replaced_text

    def _md_process(self, text: str) -> str:
        """处理文本中的 markdown 字符和换行符"""
        markdown_special_chars = {
            "#": "&#35;",
            "*": "&#42;",
            "_": "&#95;",
            "`": "&#96;",
            "[": "&#91;",
            "]": "&#93;",
            "(": "&#40;",
            ")": "&#41;",
            "~": "&#126;",
            "<": "&#60;",
            ">": "&#62;",
            "-": "&#45;",
            "+": "&#43;",
            "=": "&#61;",
            "{": "&#123;",
            "}": "&#125;",
            ".": "&#46;",
            "!": "&#33;",
        }
        for char, escaped in markdown_special_chars.items():
            text = text.replace(char, escaped)
        return self._replace_single_newline_with_double(text)

    async def _text_render(self, text: str):
        from nonebot_plugin_htmlrender import md_to_pic

        try:
            return MessageSegment.image(await md_to_pic(text, width=400))
        except Exception as e:
            raise ThemeRenderError(f"渲染文本失败: {e}")

    async def render(self, post: "Post"):
        md_text = ""

        md_text += f"###### 来源: {post.platform.name} {post.nickname or ''}\n\n"
        md_text += f"## {post.title}\n\n" if post.title else ""

        if isinstance(post, HTMLContentSupport):
            content = self._md_process(await post.get_html_content())
        else:
            content = self._md_process(await post.get_content())
        md_text += content if len(content) < 500 else f"{content[:500]}..."
        md_text += "\n\n"
        if rp := post.repost:
            md_text += f"> 转发自 {f'**{rp.nickname}**' if rp.nickname else ''}:  \n"
            md_text += f"> {rp.title}  \n" if rp.title else ""
            if isinstance(rp, HTMLContentSupport):
                rp_content = self._md_process(await rp.get_html_content())
            else:
                rp_content = self._md_process(await rp.get_content())

            md_text += (
                ">  \n> " + rp_content
                if len(rp_content) < 500
                else f"{rp_content[:500]}..." + "  \n"
            )
        md_text += "\n\n"

        msgs: list[MessageSegment] = [await self._text_render(md_text)]

        urls: list[str] = []
        if rp and rp.url:
            urls.append(f"转发详情: {rp.url}")
        if post.url:
            urls.append(f"详情: {post.url}")

        if urls:
            msgs.append(MessageSegment.text("\n".join(urls)))

        pics_group: list[Sequence[str | bytes | Path | BytesIO]] = []
        if post.images:
            pics_group.append(post.images)
        if rp and rp.images:
            pics_group.append(rp.images)

        client = await post.platform.ctx.get_client_for_static()

        for pics in pics_group:
            if is_pics_mergable(pics):
                pics = await pic_merge(list(pics), client)
            msgs.extend(map(MessageSegment.image, pics))

        return msgs
