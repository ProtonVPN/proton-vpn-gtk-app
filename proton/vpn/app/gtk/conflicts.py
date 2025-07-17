"""
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
from typing import Union, Any, Optional
from dataclasses import dataclass

from proton.vpn.app.gtk.config import AppConfig
from proton.vpn.core.settings import Settings
from proton.vpn import logging

logger = logging.getLogger(__name__)

WIREGUARD_PROTOCOL = "wireguard"

SPLIT_TUNNEL_CONFLICT_LABEL = "Enable split tunneling?"
SPLIT_TUNNEL_PROTOCOL_CONFLICT = "•  This will automatically set your "\
                                 "protocol to WireGuard."
SPLIT_TUNNEL_KILLSWITCH_CONFLICT = "•  This will disable kill switch."

KILLSWITCH_CONFLICT_LABEL = "Enable kill switch?"
KILLSWITCH_CONFLICT = "•  This will disable split tunneling."

PROTOCOL_CONFLICT_LABEL = "Disable WireGuard?"
PROTOCOL_CONFLICT = "•  This will disable split tunneling."


@dataclass
class Conflict:
    """
    Represents a conflict in settings.
    Contains a label and a description of the conflict.
    """
    label: str = ""
    description: str = ""

    def __bool__(self):
        return bool(self.description)


class Conflicts:
    """
    Class to handle conflicts between settings.

    It provides a method to detect conflicts and a method to resolve conflicts
    by modifying the settings.
    """

    @staticmethod
    def detect(setting_type: str, setting: str, value: Any,
               settings: Union[Settings, AppConfig]) -> Optional[Conflict]:
        """
        Detects conflicts based on the setting type, setting name, value and
        current settings.
        Returns a Conflict object if a conflict is detected, otherwise None.
        """

        label = ""
        msg = []
        if setting_type == "settings":
            if setting == "features.split_tunneling.enabled" and value is True:
                label = SPLIT_TUNNEL_CONFLICT_LABEL
                if settings.protocol != WIREGUARD_PROTOCOL:
                    msg.append(SPLIT_TUNNEL_PROTOCOL_CONFLICT)
                if settings.killswitch != 0:
                    msg.append(SPLIT_TUNNEL_KILLSWITCH_CONFLICT)

            if setting == "killswitch" and value != 0:
                label = KILLSWITCH_CONFLICT_LABEL
                if settings.features.split_tunneling.enabled:
                    msg.append(KILLSWITCH_CONFLICT)

            if setting == "protocol" and value != WIREGUARD_PROTOCOL:
                label = PROTOCOL_CONFLICT_LABEL
                if settings.features.split_tunneling.enabled:
                    msg.append(PROTOCOL_CONFLICT)

        if msg:
            return Conflict(
                label=label,
                description="\n".join(msg)
            )
        return None

    @staticmethod
    def resolve(setting_type: str, setting: str, value: Any,
                settings: Union[Settings, AppConfig]) -> Union[Settings, AppConfig]:
        """
        Resolves conflicts by modifying the settings based on the setting type,
        setting name, value and current settings.
        Returns the modified settings.
        """

        # Split tunnelling conflicts
        if setting_type == "settings":
            if setting == "features.split_tunneling.enabled" and value is True:
                settings.protocol = WIREGUARD_PROTOCOL
                settings.killswitch = 0

            # Kill switch conflicts
            if setting == "killswitch" and value != 0:
                settings.features.split_tunneling.enabled = False

            # Protocol
            if setting == "protocol" and value != WIREGUARD_PROTOCOL:
                settings.features.split_tunneling.enabled = False

        return settings  # No conflicts for now, but can be extended in the future.
