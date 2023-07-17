"""
Changelog window module.


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
from typing import List

from gi.repository import Gtk

from proton.vpn.app.gtk.assets import ASSETS_PATH


class ReleaseNotesDialog(Gtk.Dialog):
    """Dialog that displays release notes for each version,
    in a human friendly way."""

    WIDTH = 450
    HEIGHT = 500
    TITLE = "Release notes"
    RELEASE_NOTES = str(ASSETS_PATH / "release_notes.md")

    def __init__(self):
        super().__init__()
        self.set_default_size(self.WIDTH, self.HEIGHT)
        self.set_title(self.TITLE)
        self.set_modal(True)

        self._content_area = self.get_content_area()

        self.build()
        self.connect("realize", lambda _: self.show_all())  # pylint: disable=no-member

    def build(self):
        """Build the release notes UI."""
        collection = ReleaseNotesCollection()
        collection.create_list(self.RELEASE_NOTES)

        viewport = Gtk.Viewport()
        viewport.add(collection)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_propagate_natural_height(True)
        scrolled_window.add(viewport)

        self._content_area.pack_start(scrolled_window, False, False, 0)


class ReleaseNotesCollection(Gtk.Box):
    """Contains a collection of `ReleaseNote` objects."""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_spacing(25)
        self.get_style_context().add_class("release-notes-collection")
        self._release_notes = []

    @property
    def release_notes(self) -> List[ReleaseNote]:
        """Returns all release notes that were added."""
        return self._release_notes

    def create_list(self, filepath: str):
        """Creates the release note based on the path provided by
        `filepath`. This does follow certain patterns:

        ##: Is a header, usually should be used only versions.
        -: Is a bullet point. These bullet points usually belong under a certain
            version, thus these are never by themselves.
        \\n: Means that the bullet points for a specific version have ended and probably
            either a new version will be coming or the file has no more content.
        """
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            lines = file.readlines()
            try:
                last_line = lines[-1]
            except IndexError as excp:
                raise RuntimeError("Release notes file is empty") from excp

        new_entry = ReleaseNote()

        for line in lines:
            self._ensure_log_line_is_valid(line)

            if self.is_last_line_from_file(last_line, line):
                new_entry.add_bullet_point(self.sanitize_log(line))
                new_entry = self._store_and_generate_new_log_entry(new_entry)
            elif self.is_title(line):
                new_entry.add_title(self.sanitize_log(line))
            elif self.is_bullet_point(line):
                new_entry.add_bullet_point(self.sanitize_log(line))
            else:
                new_entry = self._store_and_generate_new_log_entry(new_entry)

    def _ensure_log_line_is_valid(self, line: str):
        if not (line.startswith("##") or line.startswith("-") or line.startswith("\n")):
            raise RuntimeError(
                f"Invalid log line '{line}'.\n"
                "Each log line should start by '##' for headers, "
                "'-' for bullet points or "
                "'\\n' to finish a entry log."
            )

    def is_title(self, current_line: str) -> bool:
        """Returns if `current_line` is a title or not."""
        return current_line.startswith("##")

    def is_bullet_point(self, current_line: str) -> bool:
        """Returns if `current_line` is a bullet point or not."""
        return current_line.startswith("-")

    def is_last_line_from_file(self, last_line: str, current_line: str) -> bool:
        """Returns of the laste line is indeed the last line from the file.

        The reason this comparison is done this way is mainly because if we would
        do a comparison between two strigs (`current_line` and `last_line`) and there
        was another line identical to the last line, then this method would return
        `True` two times, thus messing up the UI. This way we compare against the object
        ID in memory, which is sure to be unique.
        """
        return id(last_line) == id(current_line)

    def sanitize_log(self, line: str) -> str:
        """Sanitizes the output from undesired characters to be displayed."""
        return line.replace("#", "").replace("\n", "").lstrip()

    def _store_and_generate_new_log_entry(self, current_entry):
        self._release_notes.append(current_entry)
        self.pack_start(current_entry, False, False, 0)
        return ReleaseNote()


class ReleaseNote(Gtk.Box):
    """Contains all information regarding a release note.

    A release note usually contains a `ReleaseNoteTitle` and a
    collection of `ReleaseNoteBulletPoint` that are coupled to it.
    """
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self._title = None
        self._bullet_points = []
        self.show_all()

    @property
    def title(self) -> str:
        """Returns the title of this release note."""
        return self._title.get_label()

    @property
    def bullet_points(self) -> List[str]:
        """Returns the bullet points of this release note."""
        return [bullet_point.get_label() for bullet_point in self._bullet_points]

    def add_title(self, title: str):
        """Adds the title to the current `ReleaseNote` object."""
        self._title = Gtk.Label(label=title)
        self._title.set_halign(Gtk.Align.START)
        self._title.set_use_markup(True)
        self._title.get_style_context().add_class("heading")

        self.pack_start(self._title, False, False, 0)

    def add_bullet_point(self, bullet_point: str):
        """Adds the bullet point to the collection of the current `ReleaseNote` object."""
        bullet_point_label = Gtk.Label(label=bullet_point)
        bullet_point_label.set_halign(Gtk.Align.FILL)
        bullet_point_label.set_line_wrap(True)
        bullet_point_label.set_max_width_chars(1)
        bullet_point_label.set_property("xalign", 0)

        self._bullet_points.append(bullet_point_label)

        self.pack_start(bullet_point_label, False, False, 0)
