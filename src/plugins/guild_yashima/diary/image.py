import numpy as np
from io import BytesIO
from pathlib import Path

from nonebot.log import logger
from PIL.Image import Image as PILImage
from PIL.Image import Resampling
from PIL.ImageFilter import GaussianBlur
from PIL import Image

from ..image import crop_image_to_square, pic_url_to_image
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


def _image_pre_process(img: PILImage, mask: PILImage) -> PILImage:
    """将预览图与蒙版合成"""
    img = crop_image_to_square(img)
    img = img.resize((210, 210), resample=2)
    img = img.rotate(29, resample=Resampling.BILINEAR, expand=True)
    img = img.filter(GaussianBlur(radius=1))  # 添加高斯模糊

    # 将待合成的图片放在和蒙版一样大的透明背景图片上
    pure_bg = Image.new(mode="RGBA", size=mask.size)
    pure_bg.paste(img, (2583, 1685))

    # 与蒙版合成
    pure_bg.putalpha(mask)
    return pure_bg


async def build_preview_image(pic_url: str) -> BytesIO:
    """渲染预览图"""
    try:
        overlay: PILImage = await pic_url_to_image(
            pic_url, http_client()
        )  # 下载图床图片
    except Exception as ex:
        logger.warning(f"无法下载图片：{ex}，将使用占位符")
        overlay: PILImage = Image.open(
            str(Path(__file__).parent / "resources" / "placeholder.png")
        ).convert("RGBA")
    background: PILImage = Image.open(
        str(Path(__file__).parent / "resources" / "bg.jpg")
    ).convert("RGBA")
    mask: PILImage = Image.open(
        str(Path(__file__).parent / "resources" / "mask.png")
    ).convert("L")
    shadow: PILImage = Image.open(
        str(Path(__file__).parent / "resources" / "shadow.png")
    ).convert("RGBA")
    title: PILImage = Image.open(
        str(Path(__file__).parent / "resources" / "title.png")
    ).convert("RGBA")

    overlay = _image_pre_process(overlay, mask)
    background.paste(overlay, (0, 0), overlay)
    background.paste(shadow, (0, 0), shadow)
    background.paste(title, (0, 0), title)

    # 添加噪点
    background = background.convert("RGB")
    noisy_img = add_noise(background, noise_intensity=60)

    image_bytes = BytesIO()
    noisy_img.save(image_bytes, format="JPEG", quality=50)
    image_bytes.seek(0)
    return image_bytes
