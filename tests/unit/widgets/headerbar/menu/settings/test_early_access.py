"""
Test early access module.


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
from unittest.mock import patch, Mock
import pytest
import proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access as early_access
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access import DistroManager, EarlyAccessDialog, EarlyAccessWidget, ToggleWidget


early_access_raw_data = {
        "names": ["test-first-supported-distro", "test-second-supported-distro"],
        "package_manager": "test-package-manager",
        "install_repo_command": "mock-install-command",
        "update_local_index_command": "mock-update-local-index-command",
        "reinstall_app_command": "mock-reinstall-command",
        "list_installed_packages_command": "mock-list-installed-packages-command",
        "stable_package_name": "mock-stable-release",
        "beta_package_name": "mock-beta-release",
        "remove_old_package": False
    }

early_access_raw_data_swap = {
        "names": "test-name",
        "package_manager": "test-package-manager-2",
        "install_repo_command": "mock-swap",
        "update_local_index_command": "mock-update-local-index-command",
        "reinstall_app_command": "mock-reinstall-command",
        "list_installed_packages_command": "mock-list-installed-packages-command",
        "stable_package_name": "mock-stable-release",
        "beta_package_name": "mock-beta-release",
        "remove_old_package": True
    }

@pytest.fixture
def mock_distro_manager():
    """Create a mocked DistroManager for testing."""
    mock = Mock(spec=DistroManager)
    mock.stable_package_name = "protonvpn-stable-release"
    mock.beta_package_name = "protonvpn-beta-release"
    return mock
class TestEarlyAccess:

    def test_dataclass_build_when_arguments_are_passed(self):
        ea_data = DistroManager(
            early_access_raw_data.get("names"),
            early_access_raw_data.get("package_manager"),
            early_access_raw_data.get("install_repo_command"),
            early_access_raw_data.get("update_local_index_command"),
            early_access_raw_data.get("reinstall_app_command"),
            early_access_raw_data.get("list_installed_packages_command"),
            early_access_raw_data.get("stable_package_name"),
            early_access_raw_data.get("beta_package_name"),
            early_access_raw_data.get("remove_old_package")            
        )

        assert ea_data.__dict__ == early_access_raw_data

    def test_build_update_command_returns_expected_string_when_called(self):
        distro_manager = DistroManager(**early_access_raw_data)
        built_cmd = distro_manager.build_update_command(package_to_remove="test_pkg1",package_to_install="test_pkg2")
        expected_cmd = "mock-install-command test_pkg2 && mock-update-local-index-command && mock-reinstall-command"
        assert built_cmd==expected_cmd

    def test_build_update_command_returns_expected_string_when_called_with_package_swap(self):
        distro_manager = DistroManager(**early_access_raw_data_swap)
        built_cmd = distro_manager.build_update_command(package_to_remove="test_pkg1",package_to_install="test_pkg2")
        expected_cmd = "mock-swap test_pkg1 test_pkg2 && mock-update-local-index-command && mock-reinstall-command"
        assert built_cmd==expected_cmd

class TestEarlyAccessDialog:

    def test_init_dialog(self):
        EarlyAccessDialog()

    def test_display_loading_view_when_passing_new_label(self):
        dialog = EarlyAccessDialog()
        assert dialog._active_view is None

        dialog.display_loading_view("test")
        assert dialog._active_view == dialog.LOADING_VIEW
        assert dialog.get_visible() is True

    def test_display_status_view_when_passing_new_label(self):
        dialog = EarlyAccessDialog()
        assert dialog._active_view is None

        dialog.display_status_view("test")
        assert dialog._active_view == dialog.STATUS_VIEW
        assert dialog.get_visible() is True


class TestEarlyAccessWidget:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessWidget._find_installed_repo_packages")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.shutil.which")
    @pytest.mark.parametrize("which_return,installed_repo_packages,compat_distros,can_early_access_be_displayed", [
        pytest.param(True, (True, False), ["ubuntu", "debian"], True),
        pytest.param(True, (False, True), ["debian"], True),
        pytest.param(True, (True, True), ["fedora"], True),
        pytest.param(False, (True, True), ["ubuntu", "debian"], False),     # package manager not found
        pytest.param(False, (False, True), ["ubuntu", "debian"], False),    # package manager not found
        pytest.param(False, (False, False), ["ubuntu", "debian"], False),   # package manager not found, stable and beta not installed
        pytest.param(True, (False, False), ["ubuntu", "debian"], False),    # stable and beta not installed
        pytest.param(True, (True, False), ["slackware"], False),            # unsupported distro
        pytest.param(True, (False, True), ["gentoo"], False),               # unsupported distro
        pytest.param(True, (False, True), ["opensuse", "sles"], False),     # unsupported distro
        pytest.param(True, (False, True), ["", "debian"], True),            # malformed compatible distro list
        pytest.param(True, (False, True), ["", "slackware"], False)         # malformed compatible distro list
    ])
    def test_early_access_setting_is_displayed_only_when_system_requirements_are_met(
        self, mock_which, mock_find_installed_repo_packages, which_return, installed_repo_packages, compat_distros, can_early_access_be_displayed
    ):
        """This test ensures that that early access can be displayed when:
        - `distro_manager` is set to a system compatible supported configuration
        - one of the repo packages are installed, and
        - `pkexec` bin is found
        """
        with patch.object (
            early_access,
            "COMPATIBLE_DISTRIBUTIONS",
            compat_distros
        ):
            mock_which.return_value = which_return
            mock_find_installed_repo_packages.return_value = installed_repo_packages
            switch = EarlyAccessWidget(Mock(), None, Mock())

            assert switch.can_early_access_be_displayed() == can_early_access_be_displayed

    @pytest.mark.parametrize("early_access_enabled_value", [True, False])
    def test_set_initial_state_based_on_if_early_access_is_enabled_or_not(self, early_access_enabled_value):
        with patch(
            "proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessWidget.get_setting",
            return_value=early_access_enabled_value
        ):
            switch = EarlyAccessWidget(Mock(), Mock(), Mock())
            switch.set_initial_state()
            assert switch.get_property("sensitive") == early_access_enabled_value

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessWidget.get_setting")
    def test_enable_early_access(self, get_setting_mock, mock_distro_manager):
        with patch.object(ToggleWidget, '__init__', return_value=None) as mock_parent_init:
            get_setting_mock.return_value = False
            EarlyAccessWidget(Mock(), mock_distro_manager, Mock())
            callback = mock_parent_init.call_args[1]["callback"]

            callback(None, True, None)

            mock_distro_manager.build_update_command.assert_called_once_with(mock_distro_manager.stable_package_name, mock_distro_manager.beta_package_name)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessWidget.get_setting")
    def test_disable_early_access(self, get_setting_mock, mock_distro_manager):
        with patch.object(ToggleWidget, '__init__', return_value=None) as mock_parent_init:
            get_setting_mock.return_value = True
            EarlyAccessWidget(Mock(), mock_distro_manager, Mock())
            callback = mock_parent_init.call_args[1]["callback"]

            callback(None, False, None)

            mock_distro_manager.build_update_command.assert_called_once_with(mock_distro_manager.beta_package_name, mock_distro_manager.stable_package_name)
