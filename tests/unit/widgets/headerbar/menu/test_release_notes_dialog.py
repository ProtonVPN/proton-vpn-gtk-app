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
import pytest
import builtins
from unittest.mock import patch
from unittest import mock

from proton.vpn.app.gtk.widgets.headerbar.menu.release_notes_dialog import ReleaseNotesCollection, ReleaseNote

first_release_note = {
    "title": "## 4.0.0~a12",
    "bullet_point_one": "- Mock entry 12"
}

second_release_note = {
    "title": "## 4.0.0~a11",
    "bullet_point_one": "- Mock entry 11"
}

third_release_note = {
    "title": "## 4.0.0~a10",
    "bullet_point_one": "- Mock entry 10",
    "bullet_point_two": "- Mock entry 10.1"
}

MOCK_RELEASE_NOTES = f"""{first_release_note["title"]}
{first_release_note["bullet_point_one"]}

{second_release_note["title"]}
{second_release_note["bullet_point_one"]}

{third_release_note["title"]}
{third_release_note["bullet_point_one"]}
{third_release_note["bullet_point_two"]}
"""

MOCK_RELEASE_NOTES_WITH_INVALID_LINE = """## 4.0.0~a12
- Mock entry 12

invalid line
"""


@mock.patch.object(builtins, "open", new_callable=mock.mock_open, read_data=MOCK_RELEASE_NOTES_WITH_INVALID_LINE)
def test_release_notes_collection_when_creating_list_with_invalid_log_line(mock_open):
    rnc = ReleaseNotesCollection()

    with pytest.raises(RuntimeError) as e_info:
        rnc.create_list("mock_file_path")


@mock.patch.object(builtins, "open", new_callable=mock.mock_open, read_data="")
def test_release_notes_collection_when_creating_list_and_release_notes_are_empty(mock_open):
    rnc = ReleaseNotesCollection()

    with pytest.raises(RuntimeError) as e_info:
        rnc.create_list("mock_file_path")


@mock.patch.object(builtins, "open", new_callable=mock.mock_open, read_data=MOCK_RELEASE_NOTES)
def test_release_notes_collection_when_creating_list_and_notes_are_added(mock_open):

    rnc = ReleaseNotesCollection()

    first_rn = ReleaseNote()
    first_rn.add_title(rnc.sanitize_log(first_release_note["title"]))
    first_rn.add_bullet_point(rnc.sanitize_log(first_release_note["bullet_point_one"]))

    second_rn = ReleaseNote()
    second_rn.add_title(rnc.sanitize_log(second_release_note["title"]))
    second_rn.add_bullet_point(rnc.sanitize_log(second_release_note["bullet_point_one"]))

    third_rn = ReleaseNote()
    third_rn.add_title(rnc.sanitize_log(third_release_note["title"]))
    third_rn.add_bullet_point(rnc.sanitize_log(third_release_note["bullet_point_one"]))
    third_rn.add_bullet_point(rnc.sanitize_log(third_release_note["bullet_point_two"]))

    test_release_notes = [first_rn, second_rn, third_rn]

    rnc.create_list("mock_file_path")

    for release_note_from_object, release_note_from_test in zip(rnc.release_notes, test_release_notes):
        assert release_note_from_object.title == release_note_from_test.title
        assert len(release_note_from_object.bullet_points) == len(release_note_from_test.bullet_points)