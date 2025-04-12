from typing import Optional, Dict, Literal
from io import BytesIO

from wordcloud import WordCloud

from ...types import Theme
from .....utils import get_config


class Classic(Theme):
    """词云的默认主题"""

    name: Literal["classic"] = "classic"

    def prepare_options(self) -> dict:
        # 词云参数
        wordcloud_options = {}
        wordcloud_options.update(get_config()["wordcloud"]["options"])
        wordcloud_options.setdefault("width", get_config()["wordcloud"]["width"])
        wordcloud_options.setdefault("height", get_config()["wordcloud"]["height"])

        wordcloud_options.setdefault(
            "font_path", str(get_config()["wordcloud"]["font_path"])
        )
        wordcloud_options.setdefault(
            "background_color", get_config()["wordcloud"]["background_color"]
        )
        wordcloud_options.setdefault("colormap", get_config()["wordcloud"]["colormap"])
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
        image.close()
        return image_bytes
