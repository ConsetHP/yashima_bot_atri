from io import BytesIO

from httpx import AsyncClient
from PIL import Image
from PIL.Image import Image as PILImage


def crop_image_to_square(img: PILImage) -> PILImage:
    width, height = img.size
    edge_length = min(width, height)
    left = (width - edge_length) / 2
    top = (height - edge_length) / 2
    right = (width + edge_length) / 2
    bottom = (height + edge_length) / 2
    return img.crop((left, top, right, bottom))


async def pic_url_to_image(data: str | bytes, http_client: AsyncClient) -> PILImage:
    pic_buffer = BytesIO()
    if isinstance(data, str):
        res = await http_client.get(data)
        pic_buffer.write(res.content)
    else:
        pic_buffer.write(data)
    return Image.open(pic_buffer)
