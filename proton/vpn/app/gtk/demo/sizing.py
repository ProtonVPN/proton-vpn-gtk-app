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


Named values for GTK's sizing/measurement APIs, so the bare -1s they stand in
for read clearly at the call site.
"""

# Pass as a set_size_request() width or height to leave that dimension unpinned:
# GTK then sizes the widget to its own natural size on that axis instead of
# forcing a minimum.
NATURAL = -1

# The "for size" argument to Gtk.Widget.measure(): the opposite dimension is
# unconstrained, so the result is the widget's natural size on the measured axis.
UNCONSTRAINED = -1

# Returned for both baselines from a LayoutManager's do_measure() when there is
# no baseline to report.
NO_BASELINE = -1
