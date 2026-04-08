from proton.vpn.app.gtk.widgets.vpn.serverlist.city_view.server_load import ServerLoad


def test_server_load_displays_percentage_label():
    assert ServerLoad(63).get_label() == "63%"


def test_server_load_updates_label_on_set_load():
    widget = ServerLoad(10)
    widget.set_load(80)
    assert widget.get_label() == "80%"


def test_server_load_tooltip_reflects_current_load():
    assert ServerLoad(50).get_tooltip_text() == "Server load is at 50%"


def test_server_load_bar_value_matches_load():
    widget = ServerLoad(42)
    assert widget._bar.get_value() == 42


def test_server_load_applies_success_css_class_when_load_is_low():
    assert ServerLoad(50)._bar.has_css_class("signal-success")


def test_server_load_applies_warning_css_class_when_load_is_high():
    assert ServerLoad(80)._bar.has_css_class("signal-warning")


def test_server_load_applies_danger_css_class_when_load_is_critical():
    assert ServerLoad(95)._bar.has_css_class("signal-danger")


def test_server_load_removes_previous_css_class_on_set_load():
    widget = ServerLoad(50)  # success
    widget.set_load(95)      # danger
    assert not widget._bar.has_css_class("signal-success")
    assert widget._bar.has_css_class("signal-danger")


def test_server_load_boundary_75_is_success():
    assert ServerLoad(75)._bar.has_css_class("signal-success")


def test_server_load_boundary_76_is_warning():
    assert ServerLoad(76)._bar.has_css_class("signal-warning")


def test_server_load_boundary_90_is_warning():
    assert ServerLoad(90)._bar.has_css_class("signal-warning")


def test_server_load_boundary_91_is_danger():
    assert ServerLoad(91)._bar.has_css_class("signal-danger")
