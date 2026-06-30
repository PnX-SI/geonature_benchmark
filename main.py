import inspect
from functools import partial

from src.user import GeoNatureUser
from locust import events
from src import geonature, gn_modules
from logging import getLogger
logger = getLogger(__name__)

class GeoNatureBenchmarkTasks(GeoNatureUser):
    """
    Dynamically registers and manages all benchmark tasks based on the GeoNature version. Version is fetched directly from the GeoNature instance using the `host` parameter available
    in the Locust environment. 

    This class:
    - Discovers available task classes for each GeoNature module
    - Registers only tasks compatible with the detected version
    - Automatically adds tags to tasks for filtering during test runs
    
    """
    # List of all tasks to be executed during the benchmark.
    tasks = []
    # API endpoint of the GeoNature instance under test.  
    host = None 


    @classmethod
    def add_task(cls, locust_class: type[GeoNatureUser], additional_tag=None, module_url=str):
        """Extract @task decorated methods from a class and register them.

        Parameters
        ----------
            locust_class: GeoNatureUser
                Class containing task methods
            additional_tag: str, optional
                Tag to add to all discovered tasks (e.g., module name)
            module_url: str
                URL of the module to be passed to tasks
        """
        methods = inspect.getmembers(
                locust_class,
                predicate=inspect.isfunction
             )
        tasks = [method for _, method in methods if hasattr(method, 'locust_task_weight')]
        if additional_tag:
            for task in tasks:
                if not hasattr(task, 'locust_tag_set'):
                    task.locust_tag_set = set()
                task.locust_tag_set.add(additional_tag)
        tasks = cls.parametrize_tasks(tasks, module_url)
        cls.tasks.extend(tasks)
        logger.debug(f"Added following tasks to benchmark {tasks}")

    @classmethod
    def parametrize_tasks(cls, tasks, module_url):
        """
        This method is used to parametrize tasks with the module_url argument.

        If one tasks has a module_url argument, we will create another function to replace this task. This new
        function will be the same but without the parameter module_url that will be replaced by the module_url supplied
        in parametrize_tasks.

        For how the principe works, see `functools.partial` documentation or search the concept of currying.
        """
        new_tasks = []
        for task in tasks:
            if hasattr(task, 'module_url'):
                new_task = partial(task, module_url=module_url)
                new_task.locust_task_weight = getattr(task, "locust_task_weight")
                new_task.locust_tag_set = getattr(task, "locust_tag_set")
                new_tasks.append(new_task)
            else:
                new_tasks.append(task)
        return new_tasks

    
    @classmethod
    def find_class_from_version(cls, module, version):
        """Find the best-matching class for a given version of a module .
        
        Return
        ------
            The class that best matches the requested version (closest lower or equal version), or None if no suitable class is found.
        """
        classes = [
            gn_class
            for _, gn_class in inspect.getmembers(module, inspect.isclass)
            if hasattr(gn_class, "VERSION")
        ]
        classes_str= ", ".join([cls.__name__ for cls in classes])
        logger.debug(f"Classes found for module {module.__name__} : {classes_str}")
        # sort from highest version to lowest
        classes = sorted(classes, reverse=True)

        # we get the first class that supports the requested version
        for gn_class in classes:
            if gn_class.VERSION <= version:
                logger.info(f"Benchmark class used : {gn_class.__name__} (version {gn_class.VERSION})")
                return gn_class

    # GEONATURE specific methods
    def get_geonature_version(self) -> str:
        return self.get("/gn_commons/config").json().get("GEONATURE_VERSION")
    
    @classmethod
    def find_geonature_class(cls, version):
        return cls.find_class_from_version(geonature, version)

    @classmethod
    def add_geonature_tasks(cls, version: str):
        """
        Load and register GeoNature core tasks for the specified version.
        """
        geonature_class = cls.find_geonature_class(version)
        if not geonature_class:
            logger.error(f"No class supporting version {version} found for module {geonature}")
            return
        logger.debug(f"Best suited class found for geonature is {geonature_class}")
        cls.add_task(geonature_class, additional_tag="geonature")

   
    # EXTERNAL GEONATURE MODULES specific methods
    def get_modules_version(self) -> dict[str, str]:
        modules = self.get("/gn_commons/modules").json()
        return {module['module_code']: module for module in modules}

    @classmethod
    def find_modules(cls):
        modules = inspect.getmembers(gn_modules, predicate=inspect.ismodule)
        return [(name, module) for name, module in modules if hasattr(module, "MODULE_CODE")]
    
    @classmethod
    def add_modules_tasks(cls, modules_dict):
        """Load and register module-specific tasks based on available versions.

        Parameters
        ----------
            modules_dict: dict 
                Dictionary mapping module codes to their version info
        """
        geonature_modules = cls.find_modules()
        logger.debug(f"Modules we will try to add to benchmark : {geonature_modules}")
        for name, module in geonature_modules:
            if (module_infos := modules_dict.get(module.MODULE_CODE)) is None:
                logger.warning(f"Tried to launch benchmark for module {module.MODULE_CODE} but no version found for this module.")
                continue
            version = module_infos["version"]
            locust_class = cls.find_class_from_version(module, version)
            if not locust_class:
                logger.error(f"No class supporting version {version} found for module {module}")
                continue
            logger.debug(f"Best suited class found for module is {locust_class}")
            cls.add_task(locust_class, additional_tag=name, module_url=module_infos["module_url"])


@events.init.add_listener
def on_benchmark_start(environment,*args, **kwargs):
    GeoNatureBenchmarkTasks.host = environment.host
    gn_user = GeoNatureBenchmarkTasks(environment)
    gn_user.connect()
    geonature_version = gn_user.get_geonature_version()
    logger.info(f"GeoNature version detected : {geonature_version}")
    geonature_modules_version = gn_user.get_modules_version()
    for module_code, module_info in geonature_modules_version.items():
        if module_info.get("version") is not None:
            logger.info(f"Module {module_code} version detected : {module_info['version']}")
    GeoNatureBenchmarkTasks.add_geonature_tasks(geonature_version)
    GeoNatureBenchmarkTasks.add_modules_tasks(geonature_modules_version)
