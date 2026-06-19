import inspect

from src.user import GeoNatureUser
from locust import events
from src import geonature, gn_modules
from logging import getLogger
logger = getLogger(__name__)

class GeoNatureBenchmarkTasks(GeoNatureUser):
    """
    Dynamically registers and manages all benchmark tasks based on GeoNature version.

    This class:
    - Discovers available task classes for each GeoNature module
    - Registers only tasks compatible with the detected version
    - Automatically adds tags to tasks for filtering during test runs
    """
    tasks = []

    @classmethod
    def add_geonature_tasks(cls, version: str):
        """Load and register GeoNature core tasks for the specified version."""
        geonature_class = cls.find_geonature_class(version)
        if not geonature_class:
            logger.error(f"No class supporting version {version} found for module {geonature}")
            return
        logger.debug(f"Best suited class found for geonature is {geonature_class}")
        cls.add_task(geonature_class, additional_tag="geonature")

    @classmethod
    def add_modules_tasks(cls, modules_dict):
        """Load and register module-specific tasks based on available versions.

        Args:
            modules_dict: Dictionary mapping module codes to their version info
        """
        geonature_modules = cls.find_modules()
        logger.debug(f"Modules we will try to add to benchmark : {geonature_modules}")
        for name, module in geonature_modules:
            if modules_dict.get(module.MODULE_CODE) is None:
                logger.warning(f"Tryied to launch benchmark for module {module.MODULE_CODE} but no version found for this module.")
                continue
            version = modules_dict.get(module.MODULE_CODE)["version"]
            locust_class = cls.find_class_from_version(module, version)
            if not locust_class:
                logger.error(f"No class supporting version {version} found for module {module}")
                continue
            logger.debug(f"Best suited class found for module is {locust_class}")
            cls.add_task(locust_class, additional_tag=name)

    @classmethod
    def add_task(cls, locust_class: type[GeoNatureUser], additional_tag=None):
        """Extract @task decorated methods from a class and register them.

        Args:
            locust_class: Class containing task methods
            additional_tag: Tag to add to all discovered tasks (e.g., module name)
        """
        methods = inspect.getmembers(
                locust_class,
                predicate=inspect.isfunction
             )
        tasks = [method for name, method in methods if hasattr(method, 'locust_task_weight')]
        if additional_tag:
            for task in tasks:
                if not hasattr(task, 'locust_tag_set'):
                    task.locust_tag_set = {additional_tag}
                else:
                    task.locust_tag_set.add(additional_tag)
        cls.tasks.extend(tasks)
        logger.debug(f"added following tasks to benchmark {tasks}")

    @classmethod
    def find_geonature_class(cls, version):
        return cls.find_class_from_version(geonature, version)

    @classmethod
    def find_class_from_version(cls, module, version):
        """Find the best-matching class for a given version of a moduke .

        Returns the highest version class that match the target version.
        Returns None if no suitable class is found.
        """
        classes = [
            gn_class
            for _, gn_class in inspect.getmembers(module, inspect.isclass)
            if hasattr(gn_class, "VERSION")
        ]
        logger.error(f"Classes found for module {module} : {classes}")
        # sort from highest version to lowest
        classes = sorted(classes, reverse=True)

        # we get the first class that supports the requested version
        for gn_class in classes:
            if gn_class.VERSION <= version:
                return gn_class
        return None

    @classmethod
    def find_modules(cls):
        modules = inspect.getmembers(gn_modules, predicate=inspect.ismodule)
        modules = [(name, module) for name, module in modules if hasattr(module, "MODULE_CODE")]
        return modules

    def get_geonature_version(self) -> str:
        return self.get("/gn_commons/config").json().get("GEONATURE_VERSION")

    def get_modules_version(self) -> dict[str, str]:
        modules = self.get("/gn_commons/modules").json()
        modules_version = {module['module_code']: module for module in modules}
        return modules_version

@events.init.add_listener
def on_benchmark_start(environment,*args, **kwargs):
    GeoNatureBenchmarkTasks.host = environment.host
    gn_user = GeoNatureBenchmarkTasks(environment)
    gn_user.connect()
    geonature_version = gn_user.get_geonature_version()
    GeoNatureBenchmarkTasks.add_geonature_tasks(geonature_version)
    geonature_modules_version = gn_user.get_modules_version()
    GeoNatureBenchmarkTasks.add_modules_tasks(geonature_modules_version)
