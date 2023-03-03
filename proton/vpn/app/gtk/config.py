"""
App configuration module.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import os

from proton.utils.environment import VPNExecutionEnvironment

DEFAULT_APP_CONFIG = {
    "tray_pinned_servers": []
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

    @staticmethod
    def from_dict(data: dict) -> AppConfig:
        """Creates and returns `AppConfig` from the provided dict."""
        return AppConfig(
            tray_pinned_servers=data.get("tray_pinned_servers", [])
        )

    def to_dict(self) -> dict:
        """Converts the class to dict."""
        return asdict(self)

    @staticmethod
    def default() -> AppConfig:
        """Creates and returns `AppConfig` from default app configurations."""
        return AppConfig(
            tray_pinned_servers=DEFAULT_APP_CONFIG["tray_pinned_servers"]
        )
