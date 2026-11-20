"""
World map: an alternative to the server list, to pick a country or a US state
on a map. The map can be zoomed with the mouse wheel and dragged.


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
# pylint: disable=invalid-name  # Gtk and cairo callbacks use short argument names
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional

from gi.repository import Gdk, GLib

from proton.vpn.connection import states
from proton.vpn.session.servers import ServerList, TierEnum

from proton.vpn.app.gtk import Gtk
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.translator import C_
from proton.vpn.app.gtk.utils.country import get_localized_country_name
from proton.vpn.app.gtk.utils.safe_signal_connect import safe_signal_connect
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.utils import (
    make_connect_callback, make_country_connect_callback, upgrade_required_for_row
)
from proton.vpn.app.gtk.widgets.vpn.world_map.geometry import (
    MAP_ASPECT, Shape, Viewport, hit_test, load_shapes
)
from proton.vpn.app.gtk.widgets.vpn.world_map.regions import (
    ConnectedServer, Region, RegionStatus, build_regions
)

UPGRADE_URL = "https://account.protonvpn.com/"

# (red, green, blue) in [0, 1]
LAND = (0.17, 0.18, 0.23)
BORDER = (0.075, 0.082, 0.106)
STATUS_COLORS = {
    RegionStatus.AVAILABLE: (0.43, 0.29, 1.0),
    RegionStatus.CONNECTED: (0.12, 0.66, 0.52),
    RegionStatus.UPGRADE_REQUIRED: (0.33, 0.30, 0.50),
    RegionStatus.MAINTENANCE: (0.45, 0.30, 0.30),
    RegionStatus.NO_SERVER: (0.23, 0.22, 0.33),
}
HOVER_LIGHTENING = 0.18
DRAG_THRESHOLD = 4  # pixels
ZOOM_STEP = 1.25
DOT_RADIUS = 4.5  # pixels


class WorldMap(Gtk.DrawingArea):  # pylint: disable=too-many-instance-attributes
    """
    World map showing the countries (and US states) where Proton has servers.
    Clicking one offers to connect to it.
    """

    def __init__(self, controller: Controller):
        super().__init__()
        self._controller = controller
        self._user_tier: Optional[int] = None
        self._server_list: Optional[ServerList] = None
        self._connected: Optional[ConnectedServer] = None
        self._countries: List = []
        self._shapes: List[Shape] = load_shapes()
        self._regions: Dict[str, Region] = {}
        self._viewport = Viewport()
        self._hovered: Optional[Shape] = None
        self._dragging = False
        self._drag_origin = (0.0, 0.0)
        self._pointer = (0.0, 0.0)

        self.set_name("world-map")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_content_height(200)
        self.set_has_tooltip(True)
        self.set_draw_func(self._draw)

        self._popover = Gtk.Popover()
        self._popover_actions: Dict[Gtk.Button, Callable[[], None]] = {}
        self._popover.set_parent(self)
        safe_signal_connect(self, "unrealize", self._on_unrealize)

        click = Gtk.GestureClick()
        click.set_button(Gdk.BUTTON_PRIMARY)
        safe_signal_connect(click, "released", self._on_click)
        self.add_controller(click)

        drag = Gtk.GestureDrag()
        safe_signal_connect(drag, "drag-begin", self._on_drag_begin)
        safe_signal_connect(drag, "drag-update", self._on_drag_update)
        self.add_controller(drag)

        motion = Gtk.EventControllerMotion()
        safe_signal_connect(motion, "motion", self._on_motion)
        safe_signal_connect(motion, "leave", self._on_leave)
        self.add_controller(motion)

        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
        safe_signal_connect(scroll, "scroll", self._on_scroll)
        self.add_controller(scroll)

    # --- Data -----------------------------------------------------------------

    def display(self, user_tier: int, server_list: ServerList):
        """Updates the map with a new server list."""
        self._user_tier = user_tier
        self._server_list = server_list
        free_user = user_tier == TierEnum.FREE
        self._countries = server_list.group_by_country(
            group_by_location=True, include_free_servers=free_user
        )
        self._rebuild_regions()

    def connection_status_update(self, connection_state: states.State):
        """Highlights the connected country/state. Called on VPN connection changes."""
        self._connected = None
        connection = connection_state.context.connection
        if isinstance(connection_state, states.Connected) and connection \
                and self._server_list:
            server = self._server_list.get_by_id(connection.server_id)
            if server:
                self._connected = ConnectedServer(server.exit_country, server.name)
        self._rebuild_regions()

    def _rebuild_regions(self):
        if self._user_tier is None:
            return
        controller, user_tier = self._controller, self._user_tier
        self._regions = build_regions(
            self._countries,
            country_name=get_localized_country_name,
            us_state_names={s.us_state: s.name for s in self._shapes if s.us_state},
            upgrade_required=lambda row: upgrade_required_for_row(controller, user_tier, row),
            connect_country=lambda code: make_country_connect_callback(controller, code),
            connect_servers=lambda servers: make_connect_callback(
                controller, servers, user_tier
            ),
            connected=self._connected,
        )
        # Shapes without a region first, so that regions are drawn above them.
        self._shapes.sort(key=lambda shape: self._region_of(shape) is not None)
        self.queue_draw()

    def _region_of(self, shape: Shape) -> Optional[Region]:
        return self._regions.get(shape.key)

    # --- Drawing --------------------------------------------------------------

    def _draw(self, _area, cr, width, height):
        viewport = self._viewport
        viewport.resize(width, height)
        scale = viewport.zoom * viewport.scale
        origin_x, origin_y = viewport.origin

        cr.save()
        cr.translate(viewport.pan_x + viewport.zoom * origin_x,
                     viewport.pan_y + viewport.zoom * origin_y)
        cr.scale(scale, scale)
        cr.rectangle(0, 0, 1, MAP_ASPECT)  # hides what is beyond the latitudes shown
        cr.clip()
        cr.set_line_width(0.6 / scale)
        for shape in self._shapes:
            region = self._region_of(shape)
            if shape.point and not region:
                continue
            color = self._color(shape, region)
            if shape.point:
                cr.new_sub_path()
                cr.arc(*shape.map_point, DOT_RADIUS / math.sqrt(viewport.zoom) / scale,
                       0, 2 * math.pi)
                cr.set_source_rgb(*color)
                cr.fill()
                continue
            for ring in shape.map_rings:
                cr.move_to(*ring[0])
                for point in ring[1:]:
                    cr.line_to(*point)
                cr.close_path()
            cr.set_source_rgb(*color)
            cr.fill_preserve()
            cr.set_source_rgb(*BORDER)
            cr.stroke()
        cr.restore()

    def _color(self, shape: Shape, region: Optional[Region]):
        color = STATUS_COLORS[region.status] if region else LAND
        if shape is self._hovered and region:
            color = tuple(min(1.0, channel + HOVER_LIGHTENING) for channel in color)
        return color

    # --- Interaction ----------------------------------------------------------

    def _shape_at(self, x: float, y: float) -> Optional[Shape]:
        candidates = (s for s in self._shapes if self._region_of(s))
        return hit_test(candidates, self._viewport, x, y)

    def _on_motion(self, _controller, x: float, y: float):
        self._pointer = (x, y)
        shape = self._shape_at(x, y)
        if shape is self._hovered:
            return
        self._hovered = shape
        region = self._region_of(shape) if shape else None
        self.set_tooltip_text(self._label(region) if region else None)
        self.set_cursor_from_name("pointer" if region else None)
        self.queue_draw()

    def _on_leave(self, _controller):
        self._hovered = None
        self.set_tooltip_text(None)
        self.queue_draw()

    def _on_scroll(self, _controller, _dx: float, dy: float) -> bool:
        self._viewport.zoom_at(*self._pointer, ZOOM_STEP ** -dy)
        self._popover.popdown()
        self.queue_draw()
        return True

    def _on_drag_begin(self, _gesture, _x: float, _y: float):
        self._dragging = False
        self._drag_origin = (self._viewport.pan_x, self._viewport.pan_y)

    def _on_drag_update(self, _gesture, dx: float, dy: float):
        if not self._dragging and abs(dx) + abs(dy) <= DRAG_THRESHOLD:
            return
        self._dragging = True
        self._viewport.pan_x = self._drag_origin[0] + dx
        self._viewport.pan_y = self._drag_origin[1] + dy
        self._viewport.clamp()
        self.queue_draw()

    def _on_click(self, _gesture, _n_press: int, x: float, y: float):
        if self._dragging:
            self._dragging = False
            return
        shape = self._shape_at(x, y)
        if shape:
            self._show_popover(self._region_of(shape), x, y)

    # --- Popover --------------------------------------------------------------

    def _label(self, region: Region) -> str:
        if region.us_state:
            return f"{self._regions['US'].name} \u2014 {region.name}"
        return region.name

    def _show_popover(self, region: Region, x: float, y: float):
        self._popover_actions.clear()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for side in ("start", "end", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(12)
        title = Gtk.Label(label=region.name)
        title.add_css_class("heading")
        box.append(title)
        if region.us_state:
            box.append(Gtk.Label(label=self._regions["US"].name))

        self._add_actions(box, region)
        country = self._regions.get(region.country_code)
        if region.us_state and country and country is not region:
            self._add_country_action(box, region, country)

        self._popover.set_child(box)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        self._popover.set_pointing_to(rect)
        self._popover.popup()

    def _add_actions(self, box: Gtk.Box, region: Region):
        status = region.status
        if status is RegionStatus.CONNECTED:
            self._add_button(box, C_("button", "Disconnect"), "danger", self._disconnect)
        elif status is RegionStatus.AVAILABLE:
            self._add_button(
                box, C_("button", "Connect"), "primary", region.on_connect
            )
        elif status is RegionStatus.UPGRADE_REQUIRED:
            box.append(Gtk.LinkButton.new_with_label(UPGRADE_URL, C_("link", "Upgrade")))
        elif status is RegionStatus.MAINTENANCE:
            box.append(Gtk.Label(label=C_("label", "Under maintenance")))
        else:
            box.append(Gtk.Label(label=C_("label", "No server in this state")))

    def _add_country_action(self, box: Gtk.Box, region: Region, country: Region):
        """Connection to the whole country, offered on US states."""
        if country.status is RegionStatus.AVAILABLE:
            self._add_button(
                box,
                C_("button", "Connect to {country_name}").format(country_name=country.name),
                "secondary" if region.status is RegionStatus.AVAILABLE else "primary",
                country.on_connect,
            )
        elif country.status is RegionStatus.CONNECTED \
                and region.status is not RegionStatus.CONNECTED:
            self._add_button(box, C_("button", "Disconnect"), "danger", self._disconnect)

    def _add_button(self, box: Gtk.Box, label: str, css_class: str, callback):
        button = Gtk.Button(label=label)
        button.add_css_class(css_class)
        self._popover_actions[button] = callback
        safe_signal_connect(button, "clicked", self._on_action_clicked)
        box.append(button)

    def _on_action_clicked(self, button: Gtk.Button):
        self._popover.popdown()
        self._popover_actions[button]()

    def _disconnect(self):
        future = self._controller.disconnect()
        future.add_done_callback(lambda f: GLib.idle_add(f.result))

    def _on_unrealize(self, _widget):
        self._popover.unparent()
