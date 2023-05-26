"""
App configuration module.


Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, asdict
import os

from proton.utils.environment import VPNExecutionEnvironment

DEFAULT_APP_CONFIG = {
    "tray_pinned_servers": [],
    "connect_at_app_startup": None
}

APP_CONFIG = os.path.join(
    VPNExecutionEnvironment().path_config,
    "app-config.json"
)


@dataclass
class AppConfig:
    """Contains configurations that are app specific.
    """
    tray_pinned_servers: list
    connect_at_app_startup: Optional[str]

    @staticmethod
    def from_dict(data: dict) -> AppConfig:
        """Creates and returns `AppConfig` from the provided dict."""
        return AppConfig(
            tray_pinned_servers=data.get("tray_pinned_servers", []),
            connect_at_app_startup=data.get("connect_at_app_startup")
        )

    def to_dict(self) -> dict:
        """Converts the class to dict."""
        return asdict(self)

    @staticmethod
    def default() -> AppConfig:
        """Creates and returns `AppConfig` from default app configurations."""
        return AppConfig(
            tray_pinned_servers=DEFAULT_APP_CONFIG["tray_pinned_servers"],
            connect_at_app_startup=DEFAULT_APP_CONFIG["connect_at_app_startup"]
        )
