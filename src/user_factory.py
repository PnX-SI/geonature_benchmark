import os
import random
from typing import List
from pykeepass import PyKeePass


class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self._password = password


class UserFactory:
    def __init__(
        self,
        kdbx_path: str = None,
        master_password: str = None,
        group_name: str = "TestUsers",
        list_users: List[User] = [],
    ):
        if kdbx_path and master_password:
            if not os.path.exists(kdbx_path):
                raise ValueError(f"Le fichier KeePass '{kdbx_path}' n'existe pas")
            self.users = self._load(kdbx_path, master_password, group_name)
        elif len(list_users) > 0:
            self.users = list_users
        else:
            raise ValueError("Aucun utilisateur fourni")

    def _load(
        self, kdbx_path: str, master_password: str, group_name: str
    ) -> List[User]:
        """
        Charge les utilisateurs depuis un fichier KeePass.

        Parameters
        ----------
        kdbx_path : str
            Chemin vers le fichier KeePass.
        master_password : str
            Mot de passe du groupe KeePass.
        group_name : str
            Nom du groupe KeePass.

        Returns
        -------
        List[User]
            Liste des utilisateurs.
        """
        kp = PyKeePass(kdbx_path, password=master_password)

        group = kp.find_groups(name=group_name, first=True)
        if group is None:
            raise ValueError(f"Groupe '{group_name}' introuvable dans la base KeePass")

        users = []
        for entry in group.entries:
            if entry.username and entry.password:
                users.append(User(entry.username, entry.password))

        if not users:
            raise ValueError(f"Aucun utilisateur trouvé dans le groupe '{group_name}'")

        return users

    def draw_user(self) -> User:
        return random.choice(self.users)
