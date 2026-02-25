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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Données de benchmark (issues de benchmark_data.py)
# ---------------------------------------------------------------------------

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
    password = os.getenv("GEONATURE_PASSWORD", "password")

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

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, name=None, **kwargs):
        return self.client.get(url, headers=self._headers(), name=name or url, **kwargs)

    def post(self, url, name=None, **kwargs):
        return self.client.post(
            url, headers=self._headers(), name=name or url, **kwargs
        )


# ---------------------------------------------------------------------------
# Home — Statistiques générales
# ---------------------------------------------------------------------------


class TestBenchmarkHome(GeoNatureUser):
    """
    Équivalent de TestBenchmarkHome (pytest-benchmark)
    - test_general_stats       → profil user
    - test_general_stats_admin → profil admin
    """

    @tag("home")
    @task
    def test_general_stats_user(self):
        self.get("/synthese/general_stats", name="[home] general_stats (user)")

    @tag("home", "admin")
    @task
    def test_general_stats_admin(self):
        self.get("/synthese/general_stats", name="[home] general_stats (admin)")


# ---------------------------------------------------------------------------
# Métadonnées — gn_meta
# ---------------------------------------------------------------------------


class TestBenchmarkGnMeta(GeoNatureUser):
    """
    Équivalent de TestBenchmarkGnMeta (pytest-benchmark)
    - test_list_acquisition_frameworks
    - test_list_datasets
    """

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


# ---------------------------------------------------------------------------
# Synthèse
# ---------------------------------------------------------------------------

SYNTHESE_OBS_URL = "/synthese/for_web"
SYNTHESE_EXPORT_URL = "/synthese/export_observations"
SYNTHESE_EXPORT_STATUS_URL = "/synthese/export_statuts"
SYNTHESE_EXPORT_TAXON_URL = "/synthese/export_taxons"


class TestBenchmarkSynthese(GeoNatureUser):
    """
    Équivalent de TestBenchmarkSynthese (pytest-benchmark)

    Filtres géographiques / taxonomiques :
      - test_with_geometry_bbox
      - test_with_geometry_complex_poly
      - test_with_commune  (→ remplacé par un area_COM statique à adapter)
      - test_with_departement
      - test_with_region
      - test_with_up_tree_taxon
      - test_benchmark_synthese_regulation

    Exports par volume :
      - 1 000 / 10 000 / 100 000 observations
      - export status
      - export taxons
    """

    # -- Nomenclature --------------------------------------------------------

    @tag("synthese", "nomenclature")
    @task(1)
    def test_get_default_nomenclatures(self):
        self.get(
            "/synthese/defaultsNomenclatures",
            name="[synthese] get_default_nomenclatures",
        )

    # -- Filtres géométriques ------------------------------------------------

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

    # -- Filtres par aire administrative -------------------------------------
    # Les id_area ci-dessous sont des exemples ; remplace-les par les vrais ids
    # de ta base (équivalent des requêtes SQLAlchemy dans benchmark_data.py).

    @tag("synthese", "area", "commune")
    @task(2)
    def test_with_commune(self):
        self.post(
            SYNTHESE_OBS_URL,
            json={
                "modif_since_validation": False,
                "area_COM": [int(os.getenv("BENCHMARK_ID_COM", "1"))],
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
                "area_DEP": [int(os.getenv("BENCHMARK_ID_DEP", "1"))],
            },
            name="[synthese] obs departement",
        )

    @tag("synthese", "area", "region")
    @task(2)
    def test_with_region(self):
        self.post(
            SYNTHESE_OBS_URL,
            json={
                "modif_since_validation": False,
                "area_REG": [int(os.getenv("BENCHMARK_ID_REG", "1"))],
            },
            name="[synthese] obs region",
        )

    # -- Filtres taxonomiques ------------------------------------------------

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

    # -- Exports par volume --------------------------------------------------

    @tag("synthese", "export")
    @task(1)
    def test_export_observations_1000(self):
        self.post(
            SYNTHESE_EXPORT_URL,
            json={"limit": 1_000},
            name="[synthese] export obs 1 000",
        )

    @tag("synthese", "export")
    @task(1)
    def test_export_observations_10000(self):
        self.post(
            SYNTHESE_EXPORT_URL,
            json={"limit": 10_000},
            name="[synthese] export obs 10 000",
        )

    @tag("synthese", "export")
    @task(1)
    def test_export_observations_100000(self):
        self.post(
            SYNTHESE_EXPORT_URL,
            json={"limit": 100_000},
            name="[synthese] export obs 100 000",
        )

    @tag("synthese", "export")
    @task(1)
    def test_export_status(self):
        self.post(SYNTHESE_EXPORT_STATUS_URL, json={}, name="[synthese] export status")

    @tag("synthese", "export")
    @task(1)
    def test_export_taxons(self):
        self.post(SYNTHESE_EXPORT_TAXON_URL, json={}, name="[synthese] export taxons")


# ---------------------------------------------------------------------------
# OccHab
# ---------------------------------------------------------------------------


# class TestBenchmarkOcchab(GeoNatureUser):
#     """
#     Équivalent de TestBenchmarkOcchab (pytest-benchmark)
#     - test_get_station
#     - test_list_stations (admin)
#     - test_list_stations_restricted → voir TestBenchmarkOcchabRestricted
#     - test_export_all_habitats_{csv,geojson,shapefile}
#     """

#     @tag("occhab")
#     @task(1)
#     def test_get_station(self):
#         self.get("/occhab/stations/8/", name="[occhab] get_station (id=8)")

#     @tag("occhab")
#     @task(2)
#     def test_list_stations(self):
#         self.get("/occhab/stations/", name="[occhab] list_stations (admin)")

#     @tag("occhab", "export")
#     @task(1)
#     def test_export_habitats_csv(self):
#         self.post(
#             "/occhab/export_stations/csv",
#             name="[occhab] export csv",
#         )

#     @tag("occhab", "export")
#     @task(1)
#     def test_export_habitats_geojson(self):
#         self.post(
#             "/occhab/export_stations/geojson",
#             name="[occhab] export geojson",
#         )

#     @tag("occhab", "export")
#     @task(1)
#     def test_export_habitats_shapefile(self):
#         self.post(
#             "/occhab/export_stations/shapefile",
#             name="[occhab] export shapefile",
#         )


# class TestBenchmarkOcchabRestricted(GeoNatureUser):
#     """Équivalent de test_list_stations_restricted — utilisateur avec droits restreints."""

#     login = os.getenv("GEONATURE_RESTRICTED_LOGIN", "user_restricted_occhab")
#     password = os.getenv(
#         "GEONATURE_RESTRICTED_PASSWORD", os.getenv("GEONATURE_PASSWORD", "password")
#     )

#     @tag("occhab", "restricted")
#     @task
#     def test_list_stations_restricted(self):
#         self.get("/occhab/stations/", name="[occhab] list_stations (restricted)")


# ---------------------------------------------------------------------------
# OccTax
# ---------------------------------------------------------------------------


class TestBenchmarkOcctax(GeoNatureUser):
    """
    Équivalent de TestBenchmarkOcctax (pytest-benchmark)
    - test_list_releves_unrestricted (admin)
    - test_list_releves_restricted   → voir TestBenchmarkOcctaxRestricted
    """

    @tag("occtax")
    @task
    def test_list_releves_unrestricted(self):
        self.get("/occtax/releves", name="[occtax] list_releves (admin)")


class TestBenchmarkOcctaxRestricted(GeoNatureUser):
    """Équivalent de test_list_releves_restricted — utilisateur avec droits restreints."""

    login = os.getenv("GEONATURE_RESTRICTED_LOGIN", "user_restricted_occhab")
    password = os.getenv(
        "GEONATURE_RESTRICTED_PASSWORD", os.getenv("GEONATURE_PASSWORD", "password")
    )

    @tag("occtax", "restricted")
    @task
    def test_list_releves_restricted(self):
        self.get("/occtax/releves", name="[occtax] list_releves (restricted)")


# ---------------------------------------------------------------------------
# Ref Geo
# ---------------------------------------------------------------------------


class TestBenchmarkRefGeo(GeoNatureUser):
    """
    Équivalent de TestBenchmarkRefGeo (pytest-benchmark)
    - test_get_areas_with_geom
    - test_get_areas_without_geom
    """

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


class MonUtilisateur(GeoNatureUser):

    @tag("validation")
    @task
    def test_get_validated_obs(self):
        self.get("/validation/observations")

    @tag("validation")
    def test_get_last_validation(self):
        self.get("/validation/", json={"page": 1, "per_page": 20})
