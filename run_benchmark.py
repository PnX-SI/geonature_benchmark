import logging

import requests
from locust import HttpUser, between, tag, task

from src.fixture import *
from src.name_tasks import TASK_NAMES
from src.user_factory import User
import src.config as config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VERSION = "2.17.0"
# ---------------------------------------------------------------------------
# Classe de base avec authentification
# ---------------------------------------------------------------------------


class GeoNatureUser(HttpUser):
    """
    Classe de base partagée par tous les groupes de tests.
    Gère l'authentification et injecte le token Bearer dans chaque requête.
    """

    abstract = True
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = config.config.verify_ssl

    def on_start(self):
        """Récupère le token JWT au démarrage de chaque utilisateur simulé."""
        self.token = None
        user: User = config.factory.draw_user()
        with self.client.post(
            "/auth/login",
            json={"login": user.username, "password": user._password},
            name="/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("token")
                logger.info(f"Auth OK — utilisateur : {user.username}")
            else:
                resp.failure(f"Échec auth ({resp.status_code})")
        self.ids_synthese = self.fetch_ids_synthese(N_ITEM_SYNTHESE)
        self.id_area_com = self.fetch_one_area("COM", COM)
        self.id_area_dep = self.fetch_one_area("DEP", DEP)
        self.id_area_reg = self.fetch_one_area("REG", REG) if REG else None

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, name=None, **kwargs):
        return self.client.get(url, headers=self._headers(), name=name or url, **kwargs)

    def post(self, url, name=None, **kwargs):
        return self.client.post(
            url, headers=self._headers(), name=name or url, **kwargs
        )

    def fetch_ids_synthese(self, n):
        """
        helper called from tests; use plain requests so that
        the HTTP call is **not** recorded by Locust’s client.
        """
        url = self.host.rstrip("/") + SYNTHESE_OBS_URL + f"?limit={n}"
        resp = requests.get(url, headers=self._headers(), verify=self.client.verify)
        resp.raise_for_status()
        return [
            feature.get("id_synthese") for feature in resp.json().get("features", [])
        ]

    def fetch_one_area(self, type_area="COM", area_name=None):
        url = (
            self.host.rstrip("/")
            + f"/geo/areas?without_geom=true&type_code={type_area}"
        )
        if area_name:
            url += f"&area_name={area_name}"
        resp = requests.get(url, headers=self._headers(), verify=self.client.verify)
        resp.raise_for_status()
        areas = resp.json()
        return areas[0].get("id_area") if areas else None


# ---------------------------------------------------------------------------
# Synthèse
# ---------------------------------------------------------------------------

SYNTHESE_OBS_URL = "/synthese/for_web"
SYNTHESE_EXPORT_URL = "/synthese/export_observations"
SYNTHESE_EXPORT_STATUS_URL = "/synthese/export_statuts"
SYNTHESE_EXPORT_TAXON_URL = "/synthese/export_taxons"


class TestBenchmarkAll(GeoNatureUser):
    """
    Classe consolidée contenant toutes les tâches de benchmark
    Les tâches sont organisées par groupe avec des tags pour distinction.
    """

    # -- Home — Statistiques générales --

    @tag("home")
    @task
    def test_general_stats_user(self):
        self.get("/synthese/general_stats", name=TASK_NAMES["general_stats"])

    # -- Métadonnées — gn_meta --

    @tag("gn_meta")
    @task
    def test_list_acquisition_frameworks(self):
        self.get(
            "/meta/acquisition_frameworks",
            name=TASK_NAMES["acq_frameworks"],
        )

    @tag("gn_meta")
    @task
    def test_list_datasets(self):
        self.get("/meta/datasets", name=TASK_NAMES["datasets"])

    # -- Synthèse — Nomenclature --

    @tag("synthese", "nomenclature")
    @task
    def test_get_default_nomenclatures(self):
        self.get(
            "/synthese/defaultsNomenclatures", name=TASK_NAMES["default_nomenclatures"]
        )

    # -- Synthèse — Filtres géométriques --

    @tag("synthese", "geometry")
    @task
    def test_with_geometry_bbox(self):
        self.post(
            SYNTHESE_OBS_URL,
            json=BBOX_POLYGON,
            name=TASK_NAMES["obs_bbox"],
        )

    @tag("synthese", "geometry")
    @task
    def test_with_geometry_complex_poly(self):
        self.post(
            SYNTHESE_OBS_URL,
            json=COMPLEX_POLYGON,
            name=TASK_NAMES["obs_complex_poly"],
        )

    # -- Synthèse — Filtres par aire administrative --

    @tag("synthese", "area", "commune")
    @task
    def test_with_commune(self):
        self.post(
            SYNTHESE_OBS_URL,
            json={
                "modif_since_validation": False,
                "area_COM": [self.id_area_com],
            },
            name=TASK_NAMES["obs_commune"],
        )

    @tag("synthese", "area", "departement")
    @task
    def test_with_departement(self):
        self.post(
            SYNTHESE_OBS_URL,
            json={
                "modif_since_validation": False,
                "area_DEP": [self.id_area_dep],
            },
            name=TASK_NAMES["obs_dep"],
        )

    if REG:

        @tag("synthese", "area", "region")
        @task
        def test_with_region(self):
            self.post(
                SYNTHESE_OBS_URL,
                json={
                    "modif_since_validation": False,
                    "area_REG": [self.id_area_reg],
                },
                name=TASK_NAMES["obs_reg"],
            )

    # -- Synthèse — Filtres taxonomiques --

    @tag("synthese", "taxon")
    @task
    def test_with_up_tree_taxon(self):
        self.post(
            SYNTHESE_OBS_URL, json=TREE_TAXON_FILTER, name=TASK_NAMES["obs_tree_taxon"]
        )

    @tag("synthese", "regulation")
    @task
    def test_synthese_regulation(self):
        self.post(
            SYNTHESE_OBS_URL, json=REGULATION_FILTER, name=TASK_NAMES["obs_regulation"]
        )

    # -- Synthèse — Exports par volume --

    @tag("synthese", "export")
    @task
    def test_export_observations_1000(self):
        # export_observations?export_format=csv&view_name=gn_synthese.v_synthese_for_export
        self.post(
            SYNTHESE_EXPORT_URL
            + "?export_format=csv&view_name=gn_synthese.v_synthese_for_export",
            json=self.ids_synthese[:1000],
            name=TASK_NAMES["export_csv_1000"],
        )

    @tag("synthese", "export")
    @task
    def test_export_status(self):
        self.post(
            SYNTHESE_EXPORT_STATUS_URL,
            json={"id_synthese": self.ids_synthese[:N_ITEM_SYNTHESE]},
            name=TASK_NAMES["export_status"],
        )

    @tag("synthese", "export")
    @task
    def test_export_taxons(self):
        self.post(
            SYNTHESE_EXPORT_TAXON_URL,
            json=self.ids_synthese[:N_ITEM_SYNTHESE],
            name=TASK_NAMES["export_taxons"],
        )

    # -- Ref Geo --

    @tag("ref_geo")
    @task
    def test_get_areas_with_geom(self):
        self.get(
            "/geo/areas?without_geom=false&type_code=REG&type_code=DEP&type_code=COM",
            name=TASK_NAMES["geo_areas_with_geom"],
        )

    @tag("ref_geo")
    @task
    def test_get_areas_without_geom(self):
        self.get(
            "/geo/areas?without_geom=true&type_code=REG&type_code=DEP&type_code=COM",
            name=TASK_NAMES["geo_areas_without_geom"],
        )

    # -- Validation --
    if VERSION > "2.16.4":

        @tag("validation")
        @task
        def test_get_validated_obs(self):
            self.post(
                "/validation/observations",
                json={"limit": 1000},
                name=TASK_NAMES["validation_obs"],
            )

        @tag("validation")
        @task
        def test_get_last_validation(self):
            self.get(
                "/validation?page=1&per_page=10&sort=desc&order_by=validation_date&format=json&no_auto=true",
                name=TASK_NAMES["validation_last"],
            )

    else:

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
