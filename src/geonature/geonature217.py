import logging

from locust import  tag, task

from src.fixture import *
from src.name_tasks import TASK_NAMES
from src.geonature.geonature_base import GeoNatureBenchmarkBase


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeoNature2170(GeoNatureBenchmarkBase):
    VERSION = "2.17.0"
    
    @tag("validation")
    @task
    def test_get_validated_obs(self):
        self.get("/validation?limit=1000", name=TASK_NAMES["validation_obs"])

    @tag("validation")
    @task
    def test_get_last_validation(self):
        self.get(
            "/validation?page=1&per_page=10&sort=desc&order_by=last_validation.validation_date&format=json",
            name=TASK_NAMES["validation_last"],
        )