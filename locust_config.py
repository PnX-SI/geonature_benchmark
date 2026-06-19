import logging
import locust
import requests
import inspect

from src.config import *
from src.utils import compare_version, fetch_task_from_module

from src.geonature.geonature_base import GeoNatureUser
import src.geonature as geonature_task_class


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeoNatureBenchmarkTasks(GeoNatureUser):
    tasks = []

@locust.events.init.add_listener
def on_test_start(environment, **kwargs):
    geonature_version = requests.get(f"{environment.host}/gn_commons/config").json().get("GEONATURE_VERSION")

    for _, obj in inspect.getmembers(geonature_task_class, inspect.ismodule):
        tasks = fetch_task_from_module(obj, GeoNatureUser, geonature_version)
        GeoNatureBenchmarkTasks.tasks.extend(tasks)
        for task in tasks:
            logger.info(f"✅ Task {task.__name__} from module {obj.__name__} added to tasks list. 🚀")
