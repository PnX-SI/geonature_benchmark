import inspect

from src.user import GeoNatureUser
from locust import events
from src import geonature
from logging import getLogger
logger = getLogger(__name__)

class GeoNatureBenchmarkTasks(GeoNatureUser):
    """
    This class is used to dynamically add all tasks (every module to the right version) to the benchmark.
    """
    tasks = []

    @classmethod
    def add_geonature_tasks(cls, version: str):
        geonature_class = cls.find_geonature_class(version)
        logger.debug(f"Best suited class found is {geonature_class}")
        cls.add_task(geonature_class)

    @classmethod
    def add_task(cls, locust_class: type[GeoNatureUser]):
        methods = inspect.getmembers(
                locust_class,
                predicate=inspect.isfunction
             )
        tasks = [method for name, method in methods if hasattr(method, 'locust_task_weight')]
        cls.tasks.extend(tasks)
        logger.debug(f"added following tasks to benchmark {tasks}")

    @classmethod
    def find_geonature_class(cls, version):
        classes = [
            gn_class
            for _, gn_class in inspect.getmembers(geonature, inspect.isclass)
            if hasattr(gn_class, "VERSION")
        ]
        # sort from highest version to lowest
        classes = sorted(classes, reverse=True)

        # we get the first class that supports the requested version
        for gn_class in classes:
            if gn_class.VERSION <= version:
                return gn_class
        raise ValueError(f"No class supporting version {version} found")


def get_geonature_version(gn_user: GeoNatureUser):
    return gn_user.get("/gn_commons/config").json().get("GEONATURE_VERSION")


@events.init.add_listener
def on_test_start(environment,*args, **kwargs):
    GeoNatureBenchmarkTasks.host = environment.host
    gn_user = GeoNatureBenchmarkTasks(environment)
    gn_user.connect()
    geonature_version = get_geonature_version(gn_user)
    GeoNatureBenchmarkTasks.add_geonature_tasks(geonature_version)


def get_modules_version(gn_user: GeoNatureUser):
    modules = gn_user.get("/gn_commons/modules").json()
    modules_version = {module['module_code']: module.get('version', None) for module in modules}
    return modules_version