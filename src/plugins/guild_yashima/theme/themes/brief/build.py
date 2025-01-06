from typing import TYPE_CHECKING, Literal

from nonebot.adapters.onebot.v11 import MessageSegment

from ....theme import Theme, ThemeRenderUnsupportError
from ....utils import is_pics_mergable, pic_merge

if TYPE_CHECKING:
    from ....post import Post


class BriefTheme(Theme):
    """简报主题，只发送标题、头图（如果有）、URL（如果有）"""

    name: Literal["brief"] = "brief"

    async def render(self, post: "Post") -> list[MessageSegment]:
        if not post.title:
            raise ThemeRenderUnsupportError("Post has no title")
        text = f"{post.title}\n\n"
        text += f"来源: {post.platform.name} {post.nickname or ''}{' 的转发' if post.repost else ''}\n"

        urls: list[str] = []
        if (rp := post.repost) and rp.url:
            urls.append(f"转发详情: {rp.url}")
        if post.url:
            urls.append(f"详情: {post.url}")

        if urls:
            text += "\n".join(urls)

        client = await post.platform.ctx.get_client_for_static()
        msgs: list[MessageSegment] = [MessageSegment.text(text)]
        if post.images:
            pics = post.images
            if is_pics_mergable(pics):
                pics = await pic_merge(list(pics), client)
            msgs.append(MessageSegment.image(pics[0]))

        return msgs
