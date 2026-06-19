from locust import tag, task

from src.user import GeoNatureUser


class MonitoringBase(GeoNatureUser):
    VERSION = "0.0.0"

    # TODO make url modifiable by using module configuration
    @task
    def test_general_stats_user(self):
        self.get(f"/monitorings/modules", name="home")