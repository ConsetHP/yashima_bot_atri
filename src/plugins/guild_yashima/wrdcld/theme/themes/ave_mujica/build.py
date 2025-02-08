from typing import Optional, Dict, Literal
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from wordcloud import WordCloud
from wordcloud import ImageColorGenerator

from ...types import Theme
from .....utils import get_config


class AveMujica(Theme):
    """Ave Mujica 风格主题"""

    name: Literal["ave_mujica"] = "ave_mujica"

    def prepare_options(self) -> dict:
        # 词云参数
        wordcloud_options = {}
        wordcloud_options.update(get_config()["wordcloud"]["options"])
        wordcloud_options.setdefault("width", get_config()["wordcloud"]["width"])
        wordcloud_options.setdefault("height", get_config()["wordcloud"]["height"])

        wordcloud_options.setdefault("background_color", None)
        wordcloud_options.setdefault("mode", "RGBA")
        wordcloud_options.setdefault(
            "mask",
            np.array(
                Image.open(
                    str(
                        Path(__file__).parent
                        / "resources"
                        / "textures"
                        / "mask-shape.png"
                    )
                )
            ),
        )
        wordcloud_options.setdefault(
            "font_path",
            str(Path(__file__).parent / "resources" / "fonts" / "font.otf"),
        )
        wordcloud_options.setdefault(
            "color_func",
            ImageColorGenerator(
                np.array(
                    Image.open(
                        str(
                            Path(__file__).parent
                            / "resources"
                            / "textures"
                            / "mask-color.png"
                        )
                    )
                )
            ),
        )
        try:
            return wordcloud_options
        except ValueError:
            pass

    def render(
        self, frequency: Dict[str, float], wordcloud_options: dict
    ) -> Optional[BytesIO]:
        wordcloud = WordCloud(**wordcloud_options)
        image = wordcloud.generate_from_frequencies(frequency).to_image()
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        # 主题背景
        background = Image.open(
            str(Path(__file__).parent / "resources" / "textures" / "background.png")
        )
        # 词云图片
        overlay = Image.open(image_bytes)
        # 将图片覆盖到主题背景上
        background.paste(overlay, (0, 0), overlay)
        result_bytes = BytesIO()
        background.save(result_bytes, format="PNG")
        return result_bytes
