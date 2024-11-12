"""
Early access handler module.


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
import shutil
from dataclasses import dataclass
from concurrent.futures import Future
from typing import Optional, Tuple
import os
import distro
import requests
from gi.repository import Gtk, GLib, Pango
from proton.utils.environment import VPNExecutionEnvironment
from proton.vpn import logging
from proton.vpn.app.gtk.controller import Controller
from proton.vpn.app.gtk.widgets.main.loading_widget import Spinner
from proton.vpn.app.gtk.widgets.headerbar.menu.settings.common import ToggleWidget

logger = logging.getLogger(__name__)


@dataclass
class DistroManager:  # pylint: disable=too-many-instance-attributes
    """Hold data related to a specific distribution."""
    name: str
    uninstall_repo_command: str
    install_repo_command: str
    update_local_index_command: str
    reinstall_app_command: str
    list_installed_packages_command: str
    stable_url: str
    beta_url: str
    stable_package_name: str = "protonvpn-stable-release"
    beta_package_name: str = "protonvpn-beta-release"
    runtime_path: str = VPNExecutionEnvironment().path_runtime

    def download_release_package(self, url: str) -> None:
        """Builds and returns a string which contains a command to
        download a package from our repositories."""
        file = url.split("/")[-1]
        filepath = os.path.join(self.runtime_path, file)

        with requests.get(url, stream=True, timeout=2) as req:  # pylint: disable=line-too-long # noqa: E501 # nosemgrep: python.requests.best-practice.use-raise-for-status.use-raise-for-status
            req.raise_for_status()
            with open(filepath, "wb") as file:
                for chunk in req.iter_content(chunk_size=8192):
                    file.write(chunk)

    def build_uninstall_repo_command(self, package: str) -> str:
        """Builds and returns a string which contains a command to
        uninstall a package."""
        return f"{self.uninstall_repo_command} {package}"

    def build_install_repo_command(self, package: str) -> str:
        """Builds and returns a string which contains a command to
        install the downloaded."""
        return f"{self.install_repo_command} {self.runtime_path}/{package}"


DEBIAN_MANAGER = DistroManager(
    name="apt",
    uninstall_repo_command="sudo apt -y purge",
    install_repo_command="sudo apt -y install",
    list_installed_packages_command="apt list --installed",
    stable_url="https://repo.protonvpn.com/debian/dists/stable/main/binary-all/"
    "protonvpn-stable-release_1.0.4_all.deb",
    beta_url="https://repo.protonvpn.com/debian/dists/unstable/main/binary-all/"
    "protonvpn-beta-release_1.0.4_all.deb",
    update_local_index_command="sudo apt update",
    reinstall_app_command="sudo apt autoremove -y proton-vpn-gnome-desktop "
    "&& sudo apt install -y proton-vpn-gnome-desktop"
)

FEDORA_MANAGER = DistroManager(
    name="dnf",
    uninstall_repo_command="sudo dnf remove -y",
    install_repo_command="sudo dnf install -y",
    list_installed_packages_command="rpm -qa",
    stable_url=f"https://repo.protonvpn.com/fedora-{distro.version()}-"
    "stable/protonvpn-stable-release/protonvpn-stable-release-1.0.1-2.noarch.rpm",
    beta_url=f"https://repo.protonvpn.com/fedora-{distro.version()}-"
    "unstable/protonvpn-beta-release/protonvpn-beta-release-1.0.1-2.noarch.rpm",
    update_local_index_command="",
    reinstall_app_command="sudo dnf remove -y proton-vpn-gnome-desktop "
    "&& sudo dnf install -y proton-vpn-gnome-desktop"
)


class EarlyAccessDialog(Gtk.Dialog):
    """Dialog used to provide some visual feedback to the user on the status
    of early access toggle.

    It's worth noting that the dialog is not destroyed when closed but rather just hidden.
    It is destroyed only once the parent window is closed.
    """
    LOADING_VIEW = "loading"
    STATUS_VIEW = "status"
    TITLE = "Beta Access"

    def __init__(self):
        super().__init__()
        self.set_name("early-access-dialog")
        self.set_default_size(350, 200)
        self.set_modal(True)

        # We have to add a headerbar because we want to hide the close button,
        # which we don't have control otherwise.
        headerbar = Gtk.HeaderBar()
        headerbar.set_title(self.TITLE)
        headerbar.set_show_close_button(False)
        headerbar.set_decoration_layout("menu:")
        self.set_titlebar(headerbar)

        self._confirmation_button = self.add_button("_Close", Gtk.ResponseType.CLOSE)
        self._spinner = Spinner(70)
        self._spinner.set_margin_top(20)
        self._active_view = None

        self._label = Gtk.Label()
        self._label.set_width_chars(50)
        self._label.set_max_width_chars(50)
        self._label.set_line_wrap(True)
        self._label.set_line_wrap_mode(Pango.WrapMode.WORD)
        self._label.set_property("xalign", 0)

        self._confirmation_button.get_style_context().add_class("primary")

        content_area = self.get_content_area()
        content_area.set_border_width(20)  # pylint: disable=no-member
        content_area.set_spacing(20)  # pylint: disable=no-member
        content_area.pack_start(self._label, expand=False, fill=False, padding=0)
        content_area.pack_start(self._spinner, expand=False, fill=False, padding=0)

        self.connect("realize", lambda _: self.show_all())  # pylint: disable=no-member, disable=line-too-long # nosec B311, B101 # noqa: E501 # nosemgrep: python.lang.correctness.return-in-init.return-in-init

    def display_loading_view(self, new_label_value: str):
        """Displays a loading view and blocking the close button."""
        self._confirmation_button.set_property("sensitive", False)
        self._spinner.set_property("visible", True)
        self._label.set_label(new_label_value)
        self._active_view = self.LOADING_VIEW
        self.show()

    def display_status_view(self, new_label_value: str):
        """Displays a status view, allowing to close the button."""
        self._confirmation_button.set_property("sensitive", True)
        self._spinner.set_property("visible", False)
        self._label.set_label(new_label_value)
        self._active_view = self.STATUS_VIEW
        self.show()


class EarlyAccessWidget(ToggleWidget):
    """Handles all early access operations.
    It takes care of checking if package manager exists, downloading,
    uninstall and installing packages.
    """
    SUPPORTED_DISTRO_MANAGERS = [FEDORA_MANAGER, DEBIAN_MANAGER]
    DISABLE_BETA_ACCESS_MESSAGE = "Disabling Beta access..."
    ENABLE_BETA_ACCESS_MESSAGE = "Enabling Beta access..."
    UNABLE_TO_DOWNLOAD_REPO_PACKAGE_MESSAGE = "Unable to download package from repository."
    BETA_LABEL = "Beta access"
    BETA_DESCRIPTION = "Get early access and help us test new versions of Proton VPN."

    def __init__(
        self, controller: Controller,
        distro_manager: DistroManager = None,
        early_access_dialog: EarlyAccessDialog = None,
    ):
        self._distro_manager = distro_manager

        super().__init__(
            controller=controller,
            title=self.BETA_LABEL,
            description=self.BETA_DESCRIPTION,
            setting_name=None,
            requires_subscription_to_be_active=False,
            callback=self._on_switch_early_access_state
        )
        self._controller = controller
        self._dialog = early_access_dialog or EarlyAccessDialog()
        self._dialog.connect("response", lambda w, _: w.hide())  # pylint: disable=no-member, disable=line-too-long # nosec B311, B101 # noqa: E501 # nosemgrep: python.lang.correctness.return-in-init.return-in-init

    @property
    def distro_manager(self) -> DistroManager:
        """Returns a distribution manager if the current one is none."""
        if self._distro_manager is None:
            self._distro_manager = self._get_system_distro_manager()

        return self._distro_manager

    def can_early_access_be_displayed(self) -> bool:
        """Determines if early access should be available."""
        # If we couldn't determine the package manager, don't show early access.
        if self.distro_manager is None:
            return False

        stable_package_installed, beta_package_installed = self._find_installed_repo_packages()

        # If we couldn't determine which release package is installed,
        # don't show early access.
        if not stable_package_installed and not beta_package_installed:
            return False

        # If we couldn't find `pkexec` binary on system, don't show early access.
        if not shutil.which("pkexec"):
            return False

        return True

    def set_initial_state(self) -> None:
        """Sets the switch initial state."""
        self.set_state(self.get_setting())

    def get_setting(self) -> bool:
        """Returns if early access is enabled, if the early access package
        was found on the system."""
        # If it's None then it means that we're running on either:
        # - Unsupported distribution
        # - Unsupported install method that does not allow to identify a package manager
        if self.distro_manager is None:
            return False

        _, beta_package_installed = self._find_installed_repo_packages()
        return beta_package_installed

    def _on_switch_early_access_state(self, _, new_value: bool, __):
        if new_value == self.get_setting():
            return

        logger.info(
            f"Early access {'enabled' if new_value else 'disabled'}.",
            category="ui",
            subcategory="early_access",
            event="toggle"
        )

        if new_value:
            self._enable_early_access()
        else:
            self._disable_early_access()

    def _disable_early_access(self) -> None:
        """Disables early access."""
        self._dialog.display_loading_view(self.DISABLE_BETA_ACCESS_MESSAGE)
        self._process(
            self.distro_manager.stable_url,
            self.distro_manager.beta_package_name
        )

    def _enable_early_access(self) -> None:
        """Enables early access."""
        self._dialog.display_loading_view(self.ENABLE_BETA_ACCESS_MESSAGE)
        self._process(
            self.distro_manager.beta_url,
            self.distro_manager.stable_package_name,
            early_access_enabled=True
        )

    def _process(self, url: str, package_to_uninstall: str, early_access_enabled: bool = False):
        def _on_finish_download_release_package(_future: Future):
            try:
                _future.result()
            except requests.exceptions.RequestException:
                self._restore_switch_to_previous_state()
                self._dialog.display_status_view(
                    self.UNABLE_TO_DOWNLOAD_REPO_PACKAGE_MESSAGE
                )
            else:
                package_to_install = url.split("/")[-1]
                self._run_commands(package_to_install, package_to_uninstall, early_access_enabled)

        future = self._controller.executor.submit(
            self.distro_manager.download_release_package,
            url
        )
        future.add_done_callback(_on_finish_download_release_package)

    def _find_installed_repo_packages(self) -> Tuple[bool, bool]:
        """Returns if any of the repo packages are installed.

        If neither the beta and/or stable packages were found on the system, it points
        to the possibility that the app was installed via a 3rd party and via our official KBs.
        """
        beta_repo_package_installed = False
        stable_repo_package_installed = False

        result = self._controller\
            .run_subprocess(
                self.distro_manager.list_installed_packages_command.split()
            ).result()

        if self._command_failed(result):
            logger.warning(
                f"Unable to list repo packages: {result.stderr.decode('utf-8')}",
                category="subprocess", subcategory="command", event="run"
            )
            return stable_repo_package_installed, beta_repo_package_installed

        for entry in result.stdout.decode('utf-8').split("\n"):
            if self.distro_manager.beta_package_name in entry:
                beta_repo_package_installed = True
                continue

            if self.distro_manager.stable_package_name in entry:
                stable_repo_package_installed = True
                continue

            if stable_repo_package_installed and beta_repo_package_installed:
                break

        return stable_repo_package_installed, beta_repo_package_installed

    def _run_commands(
        self, package_to_install: str,
        package_to_uninstall: str, early_access_enabled: bool
    ) -> None:
        def on_handle_early_access(future: Future) -> None:
            result = future.result()

            if self._command_failed(result):
                logger.warning(
                    f"Unable to fulfil command: \nstderr: {result.stderr.decode('utf8')}\n"
                    f"stdout: {result.stdout.decode('utf8')}",
                    category="subprocess", subcategory="command", event="run"
                )
                self._restore_switch_to_previous_state()
                self._dialog.display_status_view(
                    "It was not possible to "
                    f"{'enable' if early_access_enabled else 'disable'} Beta access.\n"
                )
                return

            logger.info(
                f"Command successfully run: {result.stdout.decode('utf-8')}",
                category="subprocess",
                subcategory="command",
                event="run"
            )
            self._dialog.display_status_view(
                f"Beta access has been {'enabled' if early_access_enabled else 'disabled'}.\n"
                "Please restart the app for changes to take effect."
            )
        uninstall_existing_repo_command = \
            self.distro_manager.build_uninstall_repo_command(package_to_uninstall)

        install_new_repo_command = \
            self.distro_manager.build_install_repo_command(package_to_install)

        update_index_command = ""
        if self.distro_manager.update_local_index_command:
            update_index_command = f"&& {self.distro_manager.update_local_index_command}"

        full_command = \
            "pkexec sh -c '"\
            f"{uninstall_existing_repo_command} "\
            f"&& {install_new_repo_command}"\
            f"{update_index_command}"\
            f"&& {self.distro_manager.reinstall_app_command}'"

        # Requires shell access to be able to run all commands under one `pkexec` prompt.
        future = self._controller.run_subprocess(full_command, shell=True)  # noqa E501 # pylint: disable=no-member, disable=line-too-long # nosec B604 # nosemgrep: gitlab.bandit.B604
        future.add_done_callback(on_handle_early_access)

    def _get_system_distro_manager(self) -> Optional[DistroManager]:
        for supported_distro_manager in self.SUPPORTED_DISTRO_MANAGERS:
            if shutil.which(supported_distro_manager.name):
                return supported_distro_manager

        return None

    def _restore_switch_to_previous_state(self):
        GLib.idle_add(self.set_state, self.get_setting())

    def _command_failed(self, result) -> bool:
        return result.returncode != 0
