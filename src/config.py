from dataclasses import dataclass, field
import getpass
import os
from typing import Optional

from locust import events

from src.user_factory import User, UserFactory


@dataclass
class Config:
    """Centralise les paramètres passés en ligne de commande."""

    # Auth via KeePass
    kdbx_path: str = ""

    # Auth directe
    username: str = ""
    password: str = ""

    @classmethod
    def from_options(cls, opts) -> "Config":
        """Construit un Config depuis les options parsées par Locust."""
        return cls(
            kdbx_path=opts.kdbx,
            username=opts.username,
            password=opts.password,
        )

    @property
    def use_kdbx(self) -> bool:
        return bool(self.kdbx_path)

    @property
    def use_direct_auth(self) -> bool:
        return bool(self.username and self.password)

    def validate(self) -> None:
        """Lève une ValueError si la configuration est incohérente."""
        if not self.use_kdbx and not self.use_direct_auth:
            raise ValueError("Spécifie --kdbx ou --username + --password")


config: Optional[Config] = None
factory: Optional[UserFactory] = None


@events.init_command_line_parser.add_listener
def add_arguments(parser, **kwargs):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--kdbx", type=str, default="", help="Chemin vers le fichier KeePass (.kdbx)"
    )
    parser.add_argument(
        "--username",
        type=str,
        default="",
        help="Nom d'utilisateur (alternative à --kdbx)",
    )
    parser.add_argument(
        "--password", type=str, default="", help="Mot de passe (alternative à --kdbx)"
    )


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global config, factory
    config = Config.from_options(environment.parsed_options)
    config.validate()

    if config.use_kdbx:
        master_password = os.environ.get("KEEPASS_MASTER_PASSWORD") or getpass.getpass(
            "🔑 Mot de passe KeePass : "
        )
        factory = UserFactory(
            kdbx_path=config.kdbx_path,
            master_password=master_password,
            group_name="Users",
        )
    else:
        factory = UserFactory(
            list_users=[User(username=config.username, password=config.password)]
        )
