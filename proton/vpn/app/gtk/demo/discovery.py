"""
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


Demo screen discovery.

@register_demo only populates the registry as a side effect of importing the
module it lives in. This walks the demo.screens package and imports every
`*_demo` module so the decorators run before the registry is read. Idempotent:
importlib caches modules, so repeat calls do not re-run module bodies.
"""
import importlib
import pkgutil

from proton.vpn import logging
from proton.vpn.app.gtk.demo import screens as screens_package

logger = logging.getLogger(__name__)


def load_demo_screens() -> None:
    """Import every `*_demo` module under demo.screens so its decorators run."""
    for module in pkgutil.walk_packages(
        screens_package.__path__, prefix=f"{screens_package.__name__}."
    ):
        if not module.name.endswith("_demo"):
            continue
        try:
            # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
            importlib.import_module(module.name)
        except Exception:  # pylint: disable=broad-except
            # One broken demo module must not abort discovery of the rest.
            logger.warning(f"Failed to import demo module {module.name}", exc_info=True)
