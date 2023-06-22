import os
import random
from typing import Dict

import requests
import json

from proton.loader import Loader

# Force requests to ignore HTTP_PROXY/HTTPS_PROXY env vars as that's the
# default behaviour for aiohttp, and we are already using proxychains to
# redirect HTTP calls to the proxy.
_PROXIES = {
    "http": None,
    "https": None
}


class AtlasUsers:
    """
    Utility to create users on the atlas environment for testing purposes.
    """

    def __init__(self, api_timeout: int = 10):
        self._api_timeout = api_timeout
        self._base_url_lazy_loaded = None
        self._created_users = []

    def create(self, two_factor_auth_secret: str = None) -> Dict:
        """Creates a new user. If a 2FA secret is passed then 2FA is enabled."""
        random_hash = random.getrandbits(64)
        username = f"vpnlinux{random_hash}"
        url = f"{self._base_url}/quark/raw::user:create?-N={username}&--gen-keys=Curve25519&-f=json"
        if two_factor_auth_secret:
            url = f"{url}&-ts={two_factor_auth_secret}"
        user = self._parse_json_response(url)
        self._created_users.append(user)
        return user

    def add_plus_subscription(self, user_id: int) -> Dict:
        """Adds a plus subscription to the specified user."""
        url = f"{self._base_url}/quark/raw::user:create:subscription?userID={user_id}&--planID=vpn2022&-f=json"
        return self._parse_json_response(url)

    def delete(self, user_id: int):
        """Deletes the specified user."""
        url = f"{self._base_url}/quark/user:delete?-u={user_id}"
        response = requests.get(url, timeout=self._api_timeout, proxies=_PROXIES)
        if response.status_code != 200 or f"user with id {user_id} has been deleted" not in response.text:
            # Relying on the status code is unfortunately not enough.
            raise RuntimeError(
                f"Error deleting user with id {user_id}: "
                f"{response.status_code=}, {response.text=}"
            )

    def unban_all(self):
        """Unbans all users that are currently banned."""
        response = requests.get(f"{self._base_url}/quark/jail:unban", timeout=self._api_timeout, proxies=_PROXIES)
        if response.status_code != 200:
            raise RuntimeError(
                "Error unbanning all users: "
                f"{response.status_code=}, {response.text=}"
            )
    
    def cleanup(self):
        """Deletes all users that were created by this instance."""
        for user in self._created_users:
            self.delete(user_id=user["Dec_ID"])

    @property
    def _base_url(self):
        if not self._base_url_lazy_loaded:
            self._base_url_lazy_loaded = f"{self._get_atlas_base_url()}/internal"
        return self._base_url_lazy_loaded

    @staticmethod
    def _get_atlas_base_url() -> str:
        try:
            from proton.session_internal.environments import AtlasEnvironment
            environment = Loader.get("environment")
            if environment is not AtlasEnvironment:
                raise RuntimeError(
                    "Atlas environment is not set. Make sure PROTON_API_ENVIRONMENT "
                    "is set to an atlas environment (e.g. PROTON_API_ENVIRONMENT=atlas).")
            return AtlasEnvironment().http_base_url
        except ImportError as error:
            raise RuntimeError(
                "AtlasEnvironment is not available. Make sure proton-core-internal is installed."
            ) from error

    def _parse_json_response(self, url) -> Dict:
        response = requests.get(url, timeout=self._api_timeout, proxies=_PROXIES)
        if response.status_code != 200:
            raise RuntimeError(f"Error status code: {response.status_code=},{response.text=}")
        try:
            json_response = json.loads(response.text)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Error parsing quark API response: {response.text=}") from error
        return json_response
