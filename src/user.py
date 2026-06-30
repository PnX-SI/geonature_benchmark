import logging
from locust import HttpUser, between
from locust.user.users import UserMeta

from src.constants import SYNTHESE_OBS_URL
from src.fixture import N_ITEM_SYNTHESE, COM, DEP, REG
from src import config
from src.user_factory import User
from functools import total_ordering
from packaging.version import Version

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@total_ordering
class VersionMeta(UserMeta):
    """
    Métaclasse pour permettre des comparaisons simples entre deux classes contenant une version.
    Avec ça on peut faire `Geonature217 > Geonature216` par exemple.
    On peut aussi faire `Geonature217 >= "2.16.0"`.
    """
    VERSION = "0.0.0"

    def __eq__(cls, other):
        if hasattr(other, "VERSION"):
            return Version(cls.VERSION) == Version(other.VERSION)
        else:
            return Version(cls.VERSION) == Version(other)

    def __lt__(cls, other):
        if hasattr(other, "VERSION"):
            return Version(cls.VERSION) < Version(other.VERSION)
        else:
            return Version(cls.VERSION) < Version(other)

    def __hash__(cls):
        return hash(id(cls))


# ---------------------------------------------------------------------------
# Classe de base avec authentification
# ---------------------------------------------------------------------------
class GeoNatureUser(HttpUser, metaclass=VersionMeta):
    """
    Classe de base partagée par tous les groupes de tests.
    Gère l'authentification et injecte le token Bearer dans chaque requête.
    """
    VERSION = "0.0.0"
    abstract = True
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = config.config.verify_ssl


    def connect(self):
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


    def on_start(self):
        """
        We do those call on start so we don't neeed to do them multiple times across our benchmarks
        """
        self.connect()
        self.ids_synthese = self.fetch_ids_synthese(N_ITEM_SYNTHESE)
        self.id_area_com = self.fetch_one_area("COM", COM)
        self.id_area_dep = self.fetch_one_area("DEP", DEP)
        self.id_area_reg = self.fetch_one_area("REG", REG) if REG else None
        return super().on_start()


    def fetch_ids_synthese(self, n):
        """
        helper called from tests; use plain requests so that
        the HTTP call is **not** recorded by Locust’s client.
        """
        url = self.host.rstrip("/") + SYNTHESE_OBS_URL + f"?limit={n}"
        resp = self.get(url, catch_response=True)
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
        resp = self.get(url,catch_response=True)
        resp.raise_for_status()
        areas = resp.json()
        return areas[0].get("id_area") if areas else None

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, name=None, **kwargs):
        return self.client.get(url, headers=self._headers(), name=name or url, **kwargs)

    def post(self, url, name=None, **kwargs):
        return self.client.post(
            url, headers=self._headers(), name=name or url, **kwargs
        )

