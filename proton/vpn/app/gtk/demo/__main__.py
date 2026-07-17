"""
Demo mode entry point. Run as `python -m proton.vpn.app.gtk.demo`.


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

import sys

from proton.vpn.app.gtk.demo.demo_app import DemoApp


def main():
    """Runs the demo app."""
    sys.exit(DemoApp().run(sys.argv))


if __name__ == "__main__":
    main()
