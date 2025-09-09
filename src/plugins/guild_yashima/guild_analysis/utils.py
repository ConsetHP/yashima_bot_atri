from io import BytesIO

from datetime import datetime, timezone
from matplotlib.figure import Figure

from ..diary.database.operator import get_joined_time_by_user


def remove_duplicates(lst):
    return list(dict.fromkeys(lst))


def save_figure_to_bytes(figure: Figure):
    image_bytes = BytesIO()
    figure.savefig(image_bytes, format="png")
    image_bytes.seek(0)
    return image_bytes.getvalue()


def get_days_since_joined(user_id: str) -> int:
    """获取用户的入频时间"""
    joined_time = get_joined_time_by_user(user_id=user_id)
    delta = datetime.now(tz=timezone.utc) - joined_time
    return delta.days
