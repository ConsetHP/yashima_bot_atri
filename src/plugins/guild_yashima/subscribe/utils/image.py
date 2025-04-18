from collections.abc import Sequence
from functools import partial
from io import BytesIO
from typing import Literal, TypeGuard

from httpx import AsyncClient
from nonebot import logger, require
from PIL import Image
from PIL.Image import Image as PILImage
from yarl import URL

from ...utils import get_config
from ...image import crop_image_to_square, pic_url_to_image


def _check_image_square(size: tuple[int, int]) -> bool:
    return abs(size[0] - size[1]) / size[0] < 0.05


async def pic_merge(
    pics: list[str | bytes], http_client: AsyncClient
) -> list[str | bytes]:
    if len(pics) < 3:
        return pics
    elif len(pics) > 9:
        pics = [pics[i] for i in range(9)]  # 图片太多容易内存溢出

    _pic_url_to_image = partial(pic_url_to_image, http_client=http_client)

    first_image = await _pic_url_to_image(pics[0])
    if not _check_image_square(first_image.size):
        first_image = crop_image_to_square(first_image)
    if first_image.size[0] > 236:
        first_image = first_image.resize((236, 236))  # 分辨率太高容易内存溢出
    images: list[PILImage] = [first_image]
    # first row
    for i in range(1, 3):
        cur_img = await _pic_url_to_image(pics[i])
        if not _check_image_square(cur_img.size):
            cur_img = crop_image_to_square(cur_img)
        if cur_img.size[1] != images[0].size[1]:  # height not equal
            cur_img = cur_img.resize(images[0].size)
        images.append(cur_img)
    _tmp = 0
    x_coord = [0]
    for i in range(3):
        _tmp += images[i].size[0]
        x_coord.append(_tmp)
    y_coord = [0, first_image.size[1]]

    async def process_row(row: int) -> bool:
        if len(pics) < (row + 1) * 3:
            return False
        row_first_img = await _pic_url_to_image(pics[row * 3])
        if not _check_image_square(row_first_img.size):
            row_first_img = crop_image_to_square(row_first_img)
        if row_first_img.size[0] != images[0].size[0]:
            row_first_img = row_first_img.resize(images[0].size)
        image_row: list[PILImage] = [row_first_img]
        for i in range(row * 3 + 1, row * 3 + 3):
            cur_img = await _pic_url_to_image(pics[i])
            if not _check_image_square(cur_img.size):
                cur_img = crop_image_to_square(cur_img)
            if cur_img.size[1] != row_first_img.size[1]:
                cur_img = cur_img.resize(row_first_img.size)
            if cur_img.size[0] != images[i % 3].size[0]:
                cur_img = cur_img.resize(images[i % 3].size)
            image_row.append(cur_img)
        images.extend(image_row)
        y_coord.append(y_coord[-1] + row_first_img.size[1])
        return True

    if await process_row(1):
        matrix = (3, 2)
    else:
        matrix = (3, 1)
    if await process_row(2):
        matrix = (3, 3)
    logger.info("trigger merge image")
    target = Image.new("RGB", (x_coord[-1], y_coord[-1]))
    for y in range(matrix[1]):
        for x in range(matrix[0]):
            target.paste(
                images[y * matrix[0] + x],
                (x_coord[x], y_coord[y], x_coord[x + 1], y_coord[y + 1]),
            )
    target_io = BytesIO()
    target.save(target_io, "JPEG")
    pics = pics[matrix[0] * matrix[1] :]
    pics.insert(0, target_io.getvalue())

    return pics


def is_pics_mergable(imgs: Sequence) -> TypeGuard[list[str | bytes]]:
    if any(not isinstance(img, str | bytes) for img in imgs):
        return False

    url = [URL(img) for img in imgs if isinstance(img, str)]
    return all(u.scheme in ("http", "https") for u in url)


async def text_to_image(text: str) -> BytesIO:
    """使用 htmlrender 将文本渲染为图片"""
    if not get_config()["subscribe"]["text_to_image"]:
        raise ValueError("请启用配置：text_to_image")
    require("nonebot_plugin_htmlrender")
    from nonebot_plugin_htmlrender import text_to_pic

    return await text_to_pic(str(text))


async def capture_html(
    url: str,
    selector: str,
    timeout: float = 0,
    type: Literal["jpeg", "png"] = "png",
    quality: int | None = None,
    wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"]
    | None = None,
    viewport: dict = {"width": 1024, "height": 990},
    device_scale_factor: int = 2,
    **page_kwargs,
) -> bytes | None:
    """
    将给定的url网页的指定CSS选择器部分渲染成图片

    timeout: 超时时间，单位毫秒
    """
    require("nonebot_plugin_htmlrender")
    from nonebot_plugin_htmlrender import get_new_page

    assert url
    async with get_new_page(
        device_scale_factor=device_scale_factor, viewport=viewport, **page_kwargs
    ) as page:
        await page.goto(url, timeout=timeout, wait_until=wait_until)
        pic_data = await page.locator(selector).screenshot(
            type=type,
            quality=quality,
        )
        return pic_data
