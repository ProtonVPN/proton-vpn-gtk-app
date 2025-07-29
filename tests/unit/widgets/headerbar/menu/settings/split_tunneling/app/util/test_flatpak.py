import pytest
import io
from pathlib import Path
import os

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.util.get_containerized_app_data \
    import get_flatpak_executable


EXEC_WITH_DOUBLE_AT = "/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app --file-forwarding org.mock.app @@u %U @@"
EXEC_WITHOUT_DOUBLE_AT = "/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app --file-forwarding org.mock.app"
EXPECTED_RESULT = "/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=mock-app --file-forwarding org.mock.app"


def generate_desktop_content(executable: str) -> str:
    return f"""[Desktop Entry]
Name=MockApp
Exec={executable}
Terminal=false
Type=Application
Icon=org.mock.app
StartupWMClass=MockApp
Comment=Test mock app
Categories=Network;InstantMessaging;Chat;
X-Desktop-File-Install-Version=0.28
X-Flatpak-RenamedFrom=mock-app.desktop;
X-Flatpak=org.mock.app
"""


MOCK_EXPECTED_DOT_DESKTOP = Path(__file__).parent.resolve() / "mock_app.desktop"


def test_get_flatpak_app_data_executable_strips_double_at_out():
    with open(file=MOCK_EXPECTED_DOT_DESKTOP, mode="w", encoding="utf-8") as f:
        f.write(generate_desktop_content(EXEC_WITH_DOUBLE_AT))

    executable = get_flatpak_executable(str(MOCK_EXPECTED_DOT_DESKTOP))
    assert executable == EXPECTED_RESULT

    MOCK_EXPECTED_DOT_DESKTOP.unlink()


def test_get_flatpak_app_data_executable_returns_same_executable_when_it_does_not_contain_double_at():
    with open(file=MOCK_EXPECTED_DOT_DESKTOP, mode="w", encoding="utf-8") as f:
        f.write(generate_desktop_content(EXEC_WITHOUT_DOUBLE_AT))

    executable = get_flatpak_executable(str(MOCK_EXPECTED_DOT_DESKTOP))
    assert executable == EXPECTED_RESULT

    MOCK_EXPECTED_DOT_DESKTOP.unlink()
