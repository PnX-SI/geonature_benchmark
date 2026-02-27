"""
Locust benchmark pour GeoNature
Conversion des tests pytest-benchmark vers Locust

Usage:
    locust -f test.py --host=http://127.0.0.1:8000

Avec variables d'environnement :
    GEONATURE_LOGIN=admin GEONATURE_PASSWORD=secret locust -f test.py --host=http://127.0.0.1:8000

Pour cibler un groupe de tests uniquement (ex: synthese) :
    locust -f test.py --host=http://127.0.0.1:8000 --tags synthese
"""

import os
import logging
from locust import HttpUser, task, between, tag
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Données de benchmark (issues de benchmark_data.py)
# ---------------------------------------------------------------------------

VERSION = "2.17.0"

COM = "Gap"
DEP = "Hautes-Alpes"
REG = None


N_ITEM_SYNTHESE = 10000

BBOX_POLYGON = {
    "modif_since_validation": False,
    "geoIntersection": {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [5.828785, 44.632571],
                    [5.828785, 45.06773],
                    [6.625493, 45.06773],
                    [6.625493, 44.632571],
                    [5.828785, 44.632571],
                ]
            ],
        },
    },
}

COMPLEX_POLYGON = {
    "modif_since_validation": False,
    "geoIntersection": {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [6.063715, 44.968659],
                    [5.974429, 44.981293],
                    [5.955198, 44.934631],
                    [5.98256, 44.890826],
                    [6.040252, 44.867462],
                    [6.085582, 44.860646],
                    [6.125418, 44.884012],
                    [6.141901, 44.876225],
                    [6.135038, 44.837262],
                    [6.099322, 44.820697],
                    [6.064979, 44.804128],
                    [6.070473, 44.750493],
                    [6.133664, 44.731947],
                    [6.176247, 44.756341],
                    [6.189983, 44.777799],
                    [6.19273, 44.731947],
                    [6.261412, 44.737803],
                    [6.273775, 44.760243],
                    [6.319105, 44.741706],
                    [6.279269, 44.688002],
                    [6.231192, 44.656741],
                    [6.483941, 44.672375],
                    [6.396028, 44.628395],
                    [6.486688, 44.596121],
                    [6.538887, 44.655764],
                    [6.533392, 44.688981],
                    [6.500425, 44.73877],
                    [6.533392, 44.748528],
                    [6.514161, 44.790467],
                    [6.41938, 44.812887],
                    [6.488062, 44.854779],
                    [6.536139, 44.856727],
                    [6.597938, 44.894757],
                    [6.518262, 44.934648],
                    [6.437214, 44.932702],
                    [6.391881, 44.883076],
                    [6.356164, 44.86068],
                    [6.251768, 44.874311],
                    [6.284735, 44.921996],
                    [6.317703, 44.952143],
                    [6.385011, 44.964781],
                    [6.364406, 44.972557],
                    [6.449572, 44.976444],
                    [6.479792, 44.984218],
                    [6.468803, 45.027928],
                    [6.413857, 45.043461],
                    [6.336928, 45.055017],
                    [6.194069, 45.048223],
                    [6.170716, 44.952049],
                    [6.161099, 44.949131],
                    [6.063715, 44.968659],
                ]
            ],
        },
    },
}

REGULATION_FILTER = {
    "modif_since_validation": False,
    "regulations_protection_status": ["REGL"],
}

TREE_TAXON_FILTER = {
    "modif_since_validation": False,
    "cd_ref_parent": [
        183787,
        183767,
        183839,
        183840,
        183843,
        183874,
        184358,
        184357,
        184355,
        184354,
        184353,
        184367,
        184376,
        927956,
        200726,
        184350,
        184351,
        184366,
        184363,
        184362,
        184360,
        184359,
        184377,
        184379,
        184374,
        184371,
        184369,
        184368,
        184381,
        184393,
        184391,
        184390,
        184385,
        184387,
        184388,
        184378,
        184438,
        184449,
        184450,
        184493,
        1007942,
        184501,
        184486,
        184488,
        184491,
        184499,
        184492,
        184494,
        200765,
        184737,
        184740,
        184743,
        184752,
        184756,
        184762,
        184766,
        184767,
        184768,
        184771,
        184773,
        184775,
        184776,
        184772,
        184615,
    ],
}

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

    # Credentials par défaut, surchargés via variables d'environnement
    login = os.getenv("GEONATURE_LOGIN", "admin")
    password = os.getenv("GEONATURE_PASSWORD", "admin")

    def on_start(self):
        """Récupère le token JWT au démarrage de chaque utilisateur simulé."""
        self.token = None
        with self.client.post(
            "/auth/login",
            json={"login": self.login, "password": self.password},
            name="/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("token")
                logger.info(f"Auth OK — utilisateur : {self.login}")
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
        resp = requests.get(url, headers=self._headers())
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
        resp = requests.get(url, headers=self._headers())
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
        self.get("/synthese/general_stats", name="[home] general_stats (user)")

    @tag("home", "admin")
    @task
    def test_general_stats_admin(self):
        self.get("/synthese/general_stats", name="[home] general_stats (admin)")

    # -- Métadonnées — gn_meta --

    @tag("gn_meta")
    @task
    def test_list_acquisition_frameworks(self):
        self.get(
            "/meta/acquisition_frameworks",
            name="[gn_meta] list_acquisition_frameworks",
        )

    @tag("gn_meta")
    @task
    def test_list_datasets(self):
        self.get("/meta/datasets", name="[gn_meta] list_datasets")

    # -- Synthèse — Nomenclature --

    @tag("synthese", "nomenclature")
    @task(1)
    def test_get_default_nomenclatures(self):
        self.get(
            "/synthese/defaultsNomenclatures",
            name="[synthese] get_default_nomenclatures",
        )

    # -- Synthèse — Filtres géométriques --

    @tag("synthese", "geometry")
    @task(3)
    def test_with_geometry_bbox(self):
        self.post(SYNTHESE_OBS_URL, json=BBOX_POLYGON, name="[synthese] obs bbox")

    @tag("synthese", "geometry")
    @task(3)
    def test_with_geometry_complex_poly(self):
        self.post(
            SYNTHESE_OBS_URL,
            json=COMPLEX_POLYGON,
            name="[synthese] obs complex polygon",
        )

    # -- Synthèse — Filtres par aire administrative --

    @tag("synthese", "area", "commune")
    @task(2)
    def test_with_commune(self):
        self.post(
            SYNTHESE_OBS_URL,
            json={
                "modif_since_validation": False,
                "area_COM": [self.id_area_com],
            },
            name="[synthese] obs commune",
        )

    @tag("synthese", "area", "departement")
    @task(2)
    def test_with_departement(self):
        self.post(
            SYNTHESE_OBS_URL,
            json={
                "modif_since_validation": False,
                "area_DEP": [self.id_area_dep],
            },
            name="[synthese] obs departement",
        )

    if REG:

        @tag("synthese", "area", "region")
        @task(2)
        def test_with_region(self):
            self.post(
                SYNTHESE_OBS_URL,
                json={
                    "modif_since_validation": False,
                    "area_REG": [self.id_area_reg],
                },
                name="[synthese] obs region",
            )

    # -- Synthèse — Filtres taxonomiques --

    @tag("synthese", "taxon")
    @task(2)
    def test_with_up_tree_taxon(self):
        self.post(
            SYNTHESE_OBS_URL, json=TREE_TAXON_FILTER, name="[synthese] obs tree taxon"
        )

    @tag("synthese", "regulation")
    @task(1)
    def test_synthese_regulation(self):
        self.post(
            SYNTHESE_OBS_URL, json=REGULATION_FILTER, name="[synthese] obs regulation"
        )

    # -- Synthèse — Exports par volume --

    @tag("synthese", "export")
    @task(1)
    def test_export_observations_1000(self):
        # export_observations?export_format=csv&view_name=gn_synthese.v_synthese_for_export
        self.post(
            SYNTHESE_EXPORT_URL
            + "?export_format=csv&view_name=gn_synthese.v_synthese_for_export",
            name="[synthese] export obs 1 000",
            json=self.ids_synthese[:1000],
        )

    @tag("synthese", "export")
    @task(1)
    def test_export_status(self):
        self.post(
            SYNTHESE_EXPORT_STATUS_URL,
            json={"id_synthese": self.ids_synthese[:N_ITEM_SYNTHESE]},
            name="[synthese] export status",
        )

    @tag("synthese", "export")
    @task(1)
    def test_export_taxons(self):
        self.post(
            SYNTHESE_EXPORT_TAXON_URL,
            json=self.ids_synthese[:N_ITEM_SYNTHESE],
            name="[synthese] export taxons",
        )

    # -- OccTax --

    @tag("occtax")
    @task
    def test_list_releves_unrestricted(self):
        self.get("/occtax/releves", name="[occtax] list_releves (admin)")

    # -- Ref Geo --

    @tag("ref_geo")
    @task
    def test_get_areas_with_geom(self):
        self.get(
            "/geo/areas?without_geom=false&type_code=REG&type_code=DEP&type_code=COM",
            name="[ref_geo] get_areas with_geom",
        )

    @tag("ref_geo")
    @task
    def test_get_areas_without_geom(self):
        self.get(
            "/geo/areas?without_geom=true&type_code=REG&type_code=DEP&type_code=COM",
            name="[ref_geo] get_areas without_geom",
        )

    # -- Validation --
    if VERSION > "2.16.4":

        @tag("validation")
        @task
        def test_get_validated_obs(self):
            self.post(
                "/validation/observations",
                name="[validation] last obs to be validated (limit 1000)",
                json={"limit": 1000},
            )

        @tag("validation")
        @task
        def test_get_last_validation(self):
            self.get(
                "/validation?page=1&per_page=10&sort=desc&order_by=validation_date&format=json&no_auto=true",
                name="[validation] last_validation widget",
            )

    else:

        @tag("validation")
        @task
        def test_get_validated_obs(self):
            self.get(
                "/validation?limit=1000",
                name="[validation] last obs to be validated (limit 1000)",
            )

        @tag("validation")
        @task
        def test_get_last_validation(self):
            self.get(
                "/validation?page=1&per_page=10&sort=desc&order_by=last_validation.validation_date&format=json",
                name="[validation] last_validation widget",
            )
