import numpy as np
from io import BytesIO
from pathlib import Path

from nonebot.log import logger
from PIL.Image import Image as PILImage
from PIL import Image

from ..image import pic_url_to_image
from ..http import http_client


def add_noise(
    img: PILImage, noise_intensity: int = 30, color_mode: str = "mono"
) -> PILImage:
    """给图片添加噪点"""
    img_np = np.array(img, dtype=np.uint8)  # 转换为 NumPy 数组
    h, w, c = img_np.shape

    # 生成噪点
    if color_mode == "mono":
        noise = np.random.randint(
            -noise_intensity, noise_intensity, (h, w, 1), dtype=np.int16
        )
        noise = np.repeat(noise, 3, axis=2)  # 复制到 3 通道
    elif color_mode == "color":
        noise = np.random.randint(
            -noise_intensity, noise_intensity, (h, w, c), dtype=np.int16
        )
    else:
        raise ValueError("color_mode 只能是 'mono' 或 'color'")

    # 添加噪点，并防止像素值溢出
    noisy_img = np.clip(img_np + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(noisy_img)


async def build_preview_image(pic_url: str) -> BytesIO:
    """渲染预览图"""
    try:
        img: PILImage = await pic_url_to_image(pic_url, http_client())  # 下载图床图片
    except Exception as ex:
        logger.warning(f"无法下载图片：{ex}，将使用占位符")
        img: PILImage = Image.open(
            str(Path(__file__).parent / "resources" / "placeholder.png")
        ).convert("RGBA")

    # 添加噪点
    img = img.convert("RGB")
    noisy_img = add_noise(img, noise_intensity=90)

    image_bytes = BytesIO()
    noisy_img.save(image_bytes, format="JPEG", quality=30)
    image_bytes.seek(0)
    return image_bytes
