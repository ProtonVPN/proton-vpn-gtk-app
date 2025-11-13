import pytest

from tests.unit.testing_utils import process_gtk_events

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.data_structures \
    import AppData


@pytest.fixture
def mock_app_data() -> AppData:
    return AppData(
        name="test-app",
        executable="test/path",
        icon_name="test-icon"
    )
