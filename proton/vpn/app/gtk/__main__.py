"""
App entry point.


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

import sys

from proton.vpn.app.gtk.app import App
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.utils.executor import AsyncExecutor


def main():
    """Runs the app."""

    with AsyncExecutor() as executor:
        controller = Controller.get(executor)
        sys.exit(App(controller).run(sys.argv))


if __name__ == "__main__":
    main()
