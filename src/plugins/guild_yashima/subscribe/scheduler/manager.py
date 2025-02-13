from nonebot.log import logger

from ..database import database
from ..database.model import SubscribeTarget
from ..platform import platform_manager
from ..types import Target as T_Target
from ..utils import Site
from ...utils import get_config

from .scheduler import Scheduler

scheduler_dict: dict[type[Site], Scheduler] = {}


async def init_scheduler():
    _schedule_class_dict: dict[type[Site], list[SubscribeTarget]] = {}
    _schedule_class_platform_dict: dict[type[Site], list[str]] = {}
    for platform in platform_manager.values():
        site = platform.site
        if not hasattr(site, "name") or not site.name:
            site.name = f"AnonymousScheduleConfig[{platform.platform_name}]"

        platform_name = platform.platform_name
        targets = await database.get_platform_target(platform_name)
        if site not in _schedule_class_dict:
            _schedule_class_dict[site] = list(targets)
        else:
            _schedule_class_dict[site].extend(targets)
        if site not in _schedule_class_platform_dict:
            _schedule_class_platform_dict[site] = [platform_name]
        else:
            _schedule_class_platform_dict[site].append(platform_name)
    for site, target_list in _schedule_class_dict.items():
        if (
            not get_config()["subscribe"]["browser_render_theme"]
            and site.require_browser
        ):
            logger.warning(f"{site.name} 需要浏览器来渲染, 将不会进入调度池")
            continue

        schedulable_args = []
        for target in target_list:
            schedulable_args.append(
                (
                    target.platform_name,
                    T_Target(target.target),
                    platform_manager[target.platform_name].use_batch,
                )
            )
        platform_name_list = _schedule_class_platform_dict[site]
        scheduler_dict[site] = Scheduler(site, schedulable_args, platform_name_list)
    database.register_add_target_hook(handle_insert_new_target)
    database.register_delete_target_hook(handle_delete_target)


async def handle_insert_new_target(platform_name: str, target: T_Target):
    platform = platform_manager[platform_name]
    scheduler_obj = scheduler_dict[platform.site]
    scheduler_obj.insert_new_schedulable(platform_name, target)


async def handle_delete_target(platform_name: str, target: T_Target):
    if platform_name not in platform_manager:
        return
    platform = platform_manager[platform_name]
    scheduler_obj = scheduler_dict[platform.site]
    scheduler_obj.delete_schedulable(platform_name, target)
