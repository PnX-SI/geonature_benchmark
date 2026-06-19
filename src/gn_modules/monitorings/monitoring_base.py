from locust import tag, task

from src.user import GeoNatureUser


class MonitoringBase(GeoNatureUser):
    VERSION = "0.0.0"

    @task
    def test_general_stats_user(self, module_url="monitorings"):
        self.get(f"/{module_url}/modules", name="home")