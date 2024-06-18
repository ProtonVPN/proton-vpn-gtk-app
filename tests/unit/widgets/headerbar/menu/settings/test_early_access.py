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
from unittest.mock import patch, Mock, PropertyMock
import pytest
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access import DistroManager, EarlyAccessDialog, EarlyAccessSwitch

@pytest.fixture
def early_access_raw_data():
    data = {
        "name": "test-package-manager",
        "uninstall_repo_command": "mock-uninstall-command",
        "install_repo_command": "mock-install-command",
        "update_local_index_command": "mock-update-local-index-command",
        "reinstall_app_command": "mock-reinstall-command",
        "list_installed_packages_command": "mock-list-installed-packages-command",
        "stable_url": "mock-stable-url",
        "beta_url": "mock-beta-url",
        "stable_package_name": "mock-stable-release",
        "beta_package_name": "mock-beta-release",
        "runtime_path": "mock-runtime-path"
    }
    return data


@pytest.fixture
def distro_manager(early_access_raw_data):
    ea_data = DistroManager(
        early_access_raw_data.get("name"),
        early_access_raw_data.get("uninstall_repo_command"),
        early_access_raw_data.get("install_repo_command"),
        early_access_raw_data.get("update_local_index_command"),
        early_access_raw_data.get("reinstall_app_command"),
        early_access_raw_data.get("list_installed_packages_command"),
        early_access_raw_data.get("stable_url"),
        early_access_raw_data.get("beta_url"),
        early_access_raw_data.get("stable_package_name"),
        early_access_raw_data.get("beta_package_name"),
        early_access_raw_data.get("runtime_path")
    )

    return ea_data


class TestEarlyAccess:

    def test_dataclass_build_when_arguments_are_passed(self, early_access_raw_data):
        ea_data = DistroManager(
            early_access_raw_data.get("name"),
            early_access_raw_data.get("uninstall_repo_command"),
            early_access_raw_data.get("install_repo_command"),
            early_access_raw_data.get("update_local_index_command"),
            early_access_raw_data.get("reinstall_app_command"),
            early_access_raw_data.get("list_installed_packages_command"),
            early_access_raw_data.get("stable_url"),
            early_access_raw_data.get("beta_url"),
            early_access_raw_data.get("stable_package_name"),
            early_access_raw_data.get("beta_package_name"),
            early_access_raw_data.get("runtime_path")
        )

        assert ea_data.__dict__ == early_access_raw_data

    def test_build_uninstall_command_returns_expected_string_when_called(self, early_access_raw_data, distro_manager):
        package = "mock-repo-package"
        generated_uninstall_command = distro_manager.build_uninstall_repo_command(package)

        assert generated_uninstall_command == f"{early_access_raw_data.get('uninstall_repo_command')} {package}"

    def test_build_install_command_returns_expected_string_when_called(self, early_access_raw_data, distro_manager):
        package = "mock-repo-package"
        generated_install_command = distro_manager.build_install_repo_command(package)

        assert generated_install_command == f"{early_access_raw_data.get('install_repo_command')} {early_access_raw_data.get('runtime_path')}/{package}"


class TestEarlyAccessDialog:

    def test_init_dialog(self):
        EarlyAccessDialog()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessDialog.show")
    def test_display_loading_view_when_passing_new_label(self, mock_show):
        dialog = EarlyAccessDialog()
        assert dialog._active_view is None

        dialog.display_loading_view("test")
        assert dialog._active_view == dialog.LOADING_VIEW
        mock_show.assert_called_once()

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessDialog.show")
    def test_display_status_view_when_passing_new_label(self, mock_show):
        dialog = EarlyAccessDialog()
        assert dialog._active_view is None

        dialog.display_status_view("test")
        assert dialog._active_view == dialog.STATUS_VIEW
        mock_show.assert_called_once()


class TestEarlyAccessSwitch:

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessSwitch._find_installed_repo_packages")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.shutil.which")
    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessSwitch._get_system_distro_manager")
    @pytest.mark.parametrize("which_return,installed_repo_packages,distro_manager,can_early_access_be_displayed", [
        pytest.param(True, (True, False), Mock(), True),
        pytest.param(True, (False, True), Mock(), True),
        pytest.param(True, (True, True), Mock(), True),
        pytest.param(False, (True, True), Mock(), False),
        pytest.param(False, (False, True), Mock(), False),
        pytest.param(False, (False, False), Mock(), False),
        pytest.param(True, (False, False), Mock(), False),
        pytest.param(True, (True, False), None, False),
        pytest.param(True, (False, True), None, False),
    ])
    def test_early_access_setting_is_displayed_only_when_system_requirements_are_met(
        self, mock_get_system_distro_manager, mock_which, mock_find_installed_repo_packages, which_return, installed_repo_packages, distro_manager, can_early_access_be_displayed
    ):
        """This test ensures that that early access can be displayed when:
        - `distro_manager` is not None, and
        - one of the repo packages are installed, and
        - `pkexec` bin is found
        """
        mock_get_system_distro_manager.return_value = distro_manager
        mock_which.return_value = which_return
        mock_find_installed_repo_packages.return_value = installed_repo_packages
        switch = EarlyAccessSwitch(Mock(), distro_manager, Mock())

        assert switch.can_early_access_be_displayed() == can_early_access_be_displayed

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessSwitch.set_state")
    @pytest.mark.parametrize("early_access_enabled_value", [True, False])
    def test_set_initial_state_based_on_if_early_access_is_enabled_or_not(self, set_state, early_access_enabled_value):
        with patch(
            "proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessSwitch.early_access_enabled",
            new_callable=PropertyMock(return_value=early_access_enabled_value)
        ):
            switch = EarlyAccessSwitch(Mock(), Mock(), Mock())
            switch.set_initial_state()
            set_state.assert_called_once_with(early_access_enabled_value)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessSwitch._process")
    def test_enable_early_access(self, mock_process, distro_manager):
        switch = EarlyAccessSwitch(Mock(), distro_manager, Mock())
        switch.enable_early_access()

        mock_process.assert_called_once_with(distro_manager.beta_url, distro_manager.stable_package_name, early_access_enabled=True)

    @patch("proton.vpn.app.gtk.widgets.headerbar.menu.settings.early_access.EarlyAccessSwitch._process")
    def test_disable_early_access(self, mock_process, distro_manager):
        switch = EarlyAccessSwitch(Mock(), distro_manager, Mock())
        switch.disable_early_access()

        mock_process.assert_called_once_with(distro_manager.stable_url, distro_manager.beta_package_name)
