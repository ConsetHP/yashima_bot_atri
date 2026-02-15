import tomllib
import json

from typing import Optional

from nonebot.log import logger
from pydantic import ValidationError

from .model import Config
from ..exceptions import InvalidConfigError


def load_config() -> Optional[Config]:
    with open("config/yashima_config.toml", "rb") as file:
        data = tomllib.load(file)
        formatted_data = json.dumps(data, indent=4)
        logger.info(f"加载config.toml结果：\n{formatted_data}")
        try:
            config = Config(**data)
        except ValidationError as ve:
            logger.error(f"配置格式错误，请检查配置文件：{ve}")
            return None
        return config


config = load_config()


def get_config() -> Config:
    if not config:
        raise InvalidConfigError
    return config


def reload_config() -> None:
    global config
    logger.info("重载配置中")
    config = load_config()
