from packaging.version import Version
import inspect

def compare_version(version1, version2, operator=">="):
    """
    Compare two version strings.
    """
    assert isinstance(version1, str) and isinstance(version2, str), "Versions must be strings"
    if operator == ">=":
        return Version(version1) >= Version(version2)
    elif operator == "<=":
        return Version(version1) <= Version(version2)
    elif operator == ">":
        return Version(version1) > Version(version2)
    elif operator == "<":
        return Version(version1) < Version(version2)
    elif operator == "==":
        return Version(version1) == Version(version2)
    elif operator == "!=":
        return Version(version1) != Version(version2)
    else:
        raise ValueError(f"Invalid operator: {operator}")
    

def fetch_task_from_module(module, base_class, geonature_version):
    """
    Fetch all tasks from a given module that are subclasses of the specified base class.
    """
    tasks = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, base_class) and obj is not base_class:
            if compare_version(obj.VERSION, geonature_version,"<="):
                for _, method_obj in inspect.getmembers(obj):
                    if inspect.isfunction(method_obj) and hasattr(method_obj, "locust_task_weight"):
                        tasks.append(method_obj)
    return tasks