from unittest.mock import Mock

import pytest

from proton.vpn.session.dataclasses.servers import SecureCoreGroup
from proton.vpn.session.servers import LogicalServer, TierEnum

from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.secure_core_row import SecureCoreRow
from proton.vpn.app.gtk.widgets.vpn.serverlist.icons import DoubleFlagIcon
from tests.unit.testing_utils import process_gtk_events


def _make_server(name="CH#1", tier=TierEnum.PLUS, load=50,
                 exit_country="NL", entry_country="CH"):
    return LogicalServer({
        "ID": 1, "Name": name, "Status": 1, "Load": load,
        "Servers": [{"Status": 1}],
        "ExitCountry": exit_country, "EntryCountry": entry_country,
        "City": "Zurich", "Tier": tier,
    })


def _displayed_row(group):
    row = SecureCoreRow()
    row.display(Mock(spec=Controller), group, TierEnum.PLUS)
    return row


def _toggled_row(group):
    row = _displayed_row(group)
    row.row_content.click_toggle_button()
    process_gtk_events()
    return row


@pytest.fixture
def secure_core_group():
    return SecureCoreGroup(servers=[_make_server()])


@pytest.fixture
def multi_server_group():
    return SecureCoreGroup(servers=[
        _make_server(name="CH#1", load=30, exit_country="NL", entry_country="CH"),
        _make_server(name="IS#1", load=60, exit_country="NL", entry_country="IS"),
    ])


def test_secure_core_row_label_is_via_secure_core(secure_core_group):
    assert _displayed_row(secure_core_group).label == "Via Secure Core"


def test_secure_core_row_server_row_label_is_via_entry_country(multi_server_group):
    server_rows = _toggled_row(multi_server_group).server_rows
    assert server_rows[0].label == "Via Switzerland"
    assert server_rows[1].label == "Via Iceland"


def test_secure_core_row_server_row_icon_is_double_flag(multi_server_group):
    server_rows = _toggled_row(multi_server_group).server_rows
    assert all(isinstance(row.icon, DoubleFlagIcon) for row in server_rows)


def test_secure_core_row_server_row_connect_tooltip_includes_both_countries(multi_server_group):
    server_rows = _toggled_row(multi_server_group).server_rows
    assert server_rows[0].connect_button_tooltip == "Connect to Netherlands via Switzerland"
    assert server_rows[1].connect_button_tooltip == "Connect to Netherlands via Iceland"


def test_secure_core_row_shows_server_rows_when_toggled(multi_server_group):
    assert len(_toggled_row(multi_server_group).server_rows) == 2


def test_secure_core_row_server_rows_show_correct_load(multi_server_group):
    server_rows = _toggled_row(multi_server_group).server_rows
    assert server_rows[0].server_load == "30%"
    assert server_rows[1].server_load == "60%"


def test_secure_core_row_hides_server_rows_on_collapse(multi_server_group):
    row = _toggled_row(multi_server_group)
    row.row_content.click_toggle_button()
    process_gtk_events()
    assert len(row.server_rows) == 0
