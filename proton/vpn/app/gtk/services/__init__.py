"""
Different services running in the background.

Currently, these services are all running on the main (GLib) event loop.
However, the goal is to extract some (like the reconnector), to a systemd service
running on separate process. But, to be able to do that, first we need a VPN daemon
process coordinating the creation/deletion of VPN connections requested by other
processes like the app, the CLI or the reconnector, once extracted to a separate
process.


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
from proton.vpn.app.gtk.services.reconnector.reconnector import VPNReconnector
from proton.vpn.app.gtk.services.vpn_data_refresher import VPNDataRefresher

__all__ = ["VPNDataRefresher", "VPNReconnector"]
