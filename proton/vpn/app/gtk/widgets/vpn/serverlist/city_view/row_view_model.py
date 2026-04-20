"""
View model for row content in the server list.


Copyright (c) 2026 Proton AG

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

from dataclasses import dataclass
from typing import Callable, Optional, Set, Tuple

from proton.vpn.app.gtk import Gtk
from proton.vpn.session.servers import ServerFeatureEnum


@dataclass
class RowViewModel:  # pylint: disable=too-many-instance-attributes
    """All display data needed by RowContent to render a server list row.

    Callers build this from their respective model objects (Country, Location,
    LogicalServer, SecureCoreGroup) so that RowContent stays abstract and
    free of model type checks.
    """

    name: str
    on_connect: Callable[[], None]
    free: bool
    under_maintenance: bool
    features: Set[ServerFeatureEnum]
    smart_routing: bool
    toggable: bool
    connect_button_tooltip: str
    upgrade_required: bool = False
    load: Optional[int] = None
    secure_core_countries: Optional[Tuple[str, str]] = None  # (entry_name, exit_name)
    icon_factory: Optional[Callable[[], Gtk.Widget]] = None
    toggle_button_tooltips: Optional[Tuple[str, str]] = None

    def __post_init__(self):
        if self.toggable and self.toggle_button_tooltips is None:
            raise ValueError("toggle_button_tooltips is required when toggable=True")
        if self.toggle_button_tooltips is not None and len(self.toggle_button_tooltips) != 2:
            raise ValueError("toggle_button_tooltips must be a tuple of exactly 2 strings")
        if self.secure_core_countries is not None and len(self.secure_core_countries) != 2:
            raise ValueError("secure_core_countries must be a tuple of exactly 2 strings")
