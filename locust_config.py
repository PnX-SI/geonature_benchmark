import logging
import locust
import requests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from src.config import *

from src.geonature.geonature_base import GeoNatureUser
import inspect
import src.geonature as geonature_task_class
from packaging.version import Version

class GeoNatureBenchmarkTasks(GeoNatureUser):
    
    tasks = []

@locust.events.init.add_listener
def on_test_start(environment, **kwargs):
    geonature_version = requests.get(f"{environment.host}/gn_commons/config").json().get("GEONATURE_VERSION")
    for _, obj in inspect.getmembers(geonature_task_class, inspect.ismodule):
            for sub_name, sub_obj in inspect.getmembers(obj):
                if inspect.isclass(sub_obj) and issubclass(sub_obj, GeoNatureUser) and sub_obj is not GeoNatureUser:
                    if Version(sub_obj.VERSION) <= Version(geonature_version):
                        for method_name, method_obj in inspect.getmembers(sub_obj):
                            if inspect.isfunction(method_obj) and hasattr(method_obj, "locust_task_weight"):
                                logger.info(f"✅ Chargement de la tâche {method_name} pour GeoNature {geonature_version} : {sub_name}")
                                GeoNatureBenchmarkTasks.tasks.append(method_obj)
