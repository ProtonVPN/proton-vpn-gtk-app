"""
Different services running in the background.

Currently, these services are all running on the main (GLib) event loop.
However, the goal is to extract some (like the reconnector), to a systemd service
running on separate process. But, to be able to do that, first we need a VPN daemon
process coordinating the creation/deletion of VPN connections requested by other
processes like the app, the CLI or the reconnector, once extracted to a separate
process.
"""
from proton.vpn.app.gtk.services.reconnector.reconnector import VPNReconnector
from proton.vpn.app.gtk.services.vpn_data_refresher import VPNDataRefresher

__all__ = ["VPNDataRefresher", "VPNReconnector"]
