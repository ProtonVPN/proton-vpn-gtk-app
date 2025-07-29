import pytest
import io
from pathlib import Path
import os

from proton.vpn.app.gtk.widgets.headerbar.menu.settings.split_tunneling.app.util.get_containerized_app_data \
    import get_snap_app_data


ICON = "/snap/test-app/198/meta/gui/test-app.png"

MOCK_EXPECTED_DOT_DESKTOP_CONTENT = f"""[Desktop Entry]
X-SnapInstanceName=test-app
Name=Some Test App
Comment=This is just a test app.
GenericName=Test App
X-SnapAppName=test-app
Exec=env BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/test_app.desktop /snap/bin/test-app --force-user-env %F
Icon={ICON}
Type=Application
StartupNotify=false
StartupWMClass=TestApp
Categories=TextEditor;Development;IDE;
MimeType=application/x-code-workspace;
Actions=new-empty-window;
Keywords=test-app;

[Desktop Action new-empty-window]
Name=New Empty Window
Name[cs]=Nové prázdné okno
Name[de]=Neues leeres Fenster
Name[es]=Nueva ventana vacía
Name[fr]=Nouvelle fenêtre vide
Name[it]=Nuova finestra vuota
Name[ja]=新しい空のウィンドウ
Name[ko]=새 빈 창
Name[ru]=Новое пустое окно
Name[zh_CN]=新建空窗口
Name[zh_TW]=開新空視窗
X-SnapAppName=test-app
Exec=env BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/test_app.desktop /snap/bin/test-app --force-user-env --new-window %F
Icon=/snap/code/198/meta/gui/test-app.png
"""

MOCK_UNEXPECTED_DOT_DESKTOP_CONTENT = f"""[Desktop Entry]
X-SnapInstanceName=test-app
Name=Some Test App
Comment=This is just a test app.
GenericName=Test App
X-SnapAppName=test-app
Exec=env BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/test_app.desktop --force-user-env %F
Icon={ICON}
Type=Application
StartupNotify=false
StartupWMClass=TestApp
Categories=TextEditor;Development;IDE;
MimeType=application/x-code-workspace;
Actions=new-empty-window;
Keywords=test-app;

[Desktop Action new-empty-window]
Name=New Empty Window
Name[cs]=Nové prázdné okno
Name[de]=Neues leeres Fenster
Name[es]=Nueva ventana vacía
Name[fr]=Nouvelle fenêtre vide
Name[it]=Nuova finestra vuota
Name[ja]=新しい空のウィンドウ
Name[ko]=새 빈 창
Name[ru]=Новое пустое окно
Name[zh_CN]=新建空窗口
Name[zh_TW]=開新空視窗
X-SnapAppName=test-app
Exec=env BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/test_app.desktop /snap/bin/test-app --force-user-env --new-window %F
Icon=/snap/code/198/meta/gui/test-app.png
"""

EXPECTED_DOT_DESKTOP_FILEPATH = Path(__file__).parent.resolve() / "test_app.desktop"
UNEXPECTED_DOT_DESKTOP_FILEPATH = Path(__file__).parent.resolve() / "test_app.desktop"


def test_get_snap_app_data_executable_returns_when_exec_field_is_present():
    with open(file=EXPECTED_DOT_DESKTOP_FILEPATH, mode="w", encoding="utf-8") as f:
        f.write(MOCK_EXPECTED_DOT_DESKTOP_CONTENT)

    executable, icon = get_snap_app_data(str(EXPECTED_DOT_DESKTOP_FILEPATH))
    assert executable == "/snap/test-app/" and icon == ICON

    EXPECTED_DOT_DESKTOP_FILEPATH.unlink()


def test_get_snap_app_data_executable_returns_none_when_exec_field_is_in_unexpected_format():
    with open(file=UNEXPECTED_DOT_DESKTOP_FILEPATH, mode="w", encoding="utf-8") as f:
        f.write(MOCK_UNEXPECTED_DOT_DESKTOP_CONTENT)

    executable, icon = get_snap_app_data(str(UNEXPECTED_DOT_DESKTOP_FILEPATH))
    assert executable is None and icon is None

    UNEXPECTED_DOT_DESKTOP_FILEPATH.unlink()
