
%define unmangled_name proton-vpn-gtk-app
%define version 4.3.1~rc2
%define upstream_version 4.3.1rc2
%define logo_filename proton-vpn-logo.svg
%define desktop_entry_filename protonvpn-app.desktop
%define release 1

Prefix: %{_prefix}
Name: %{unmangled_name}
Version: %{version}
Release: %{release}%{?dist}
Summary: %{unmangled_name} library

Group: ProtonVPN
License: GPLv3
Vendor: Proton Technologies AG <opensource@proton.me>
URL: https://github.com/ProtonVPN/%{unmangled_name}
Source0: %{unmangled_name}-%{upstream_version}.tar.gz
Source3: %{desktop_entry_filename}
Source4: %{logo_filename}
BuildArch: noarch
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot

BuildRequires: gtk3
BuildRequires: desktop-file-utils
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-gobject
BuildRequires: python3-dbus
BuildRequires: python3-proton-vpn-api-core
BuildRequires: python3-proton-vpn-logger
BuildRequires: librsvg2
BuildRequires: python3-packaging

Requires: gtk3
Requires: python3-gobject
Requires: python3-dbus
Requires: python3-proton-vpn-api-core
Requires: python3-proton-vpn-logger
Requires: librsvg2
Requires: python3-packaging
Suggests: libappindicator-gtk3

%{?python_disable_dependency_generator}

%description
Package %{unmangled_name}.

%prep
%setup -n %{unmangled_name}-%{upstream_version}

%build
python3 setup.py build

%install
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE3}
desktop-file-validate %{buildroot}%{_datadir}/applications/%{desktop_entry_filename}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
cp %{SOURCE4} %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{logo_filename}
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%files -f INSTALLED_FILES
%{python3_sitelib}/proton/
%{python3_sitelib}/proton_vpn_gtk_app-%{upstream_version}*.egg-info/
%{_datadir}/applications/%{desktop_entry_filename}
%{_datadir}/icons/hicolor/scalable/apps/%{logo_filename}
%defattr(-,root,root)

%changelog
* Thu Apr 18 2024 Luke Titley <luke.titley@proton.ch> 4.3.1~rc2
- Add connection features to the wireguard certificate request.

* Tue Apr 16 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.3.1~rc1
- Periodically refresh certificate.

* Thu Apr 11 2024 Luke Titley <luke.titley@proton.ch> 4.3.0
- Provide the possibility to disable Kill Switch if user is logged out and Kill Switch is set to permanent (Alexandru Cheltuitor)
- Ensure that protocol list in settings UI is properly capitalized and alphabetically ordered (Alexandru Cheltuitor)
- Anonymous crash reports are now sent by default, this can be disabled in the settings (Luke Titley)
- Change how we build debian and rpm packages. We now depend on a single versions.yml file to build everything (Luke Titley)
- Increase minimum number of characters required for bug report description (Luke Titley)

* Wed Feb 21 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.2.0
- Add overlay when connecting to server (Alexandru Cheltuitor)
- Upon logging out or quitting, inform the user about the kill switch status (Alexandru Cheltuitor)
- Apply kill switch settings immediately (Josep Llaneras)
- Add permanent option to kill switch setting (Alexandru Cheltuitor)
- Fix minor bug in country row initialization (Josep Llaneras)

* Fri Jan 26 2024 Josep Llaneras <josep.llaneras@proton.ch> 4.1.10
- Recover from manual cache deletion

* Wed Jan 24 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.1.9
- Improve email regex when submitting bug reports

* Mon Jan 15 2024 Josep Llaneras <josep.llaneras@proton.ch> 4.1.8
- Dispatch VPN monitor status updates from asyncio to GLib loop

* Thu Jan 11 2024 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.1.7
- Log time of search queries

* Thu Jan 11 2024 Josep Llaneras <josep.llaneras@proton.ch> 4.1.6
- Fix close button on account dialog
- Fix name duplication in tests
- Fix fedora package spec

* Tue Jan 09 2024 Josep Llaneras <josep.llaneras@proton.ch> 4.1.5
- Disconnect from VPN when quitting app

* Wed Dec 13 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.1.4
- Fix app getting stuck in disconnecting state

* Mon Nov 27 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.1.3
- Add Secure core icon to servers that support the feature

* Wed Nov 08 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.1.2
- Switch to AsyncExecutor to avoid thread-safety issues in asyncio code

* Tue Oct 31 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.1.1
- Show authentication denied error message

* Wed Oct 25 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.1.0
- Display secure core servers in server list

* Tue Oct 10 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0
- Stable release

* Fri Sep 15 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~b2
- Add account data to settings window

* Mon Sep 11 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~b1
- Fixed typos
- Official beta release

* Tue Sep 05 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a16
- Add kill switch selection to settings window

* Fri Jul 21 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a15
- Add server pinning to settings window

* Wed Jul 19 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a14
- Add NAT type selection to settings window

* Mon Jul 17 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a13
- Add user-friendly release notes to app

* Wed Jul 12 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a12
- Add auto-connect at app startup to settings window

* Thu Jul 06 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a11
- Add port forwarding selection to settings window

* Thu Jul 06 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a10
- Add netshield selection to settings window

* Wed Jul 05 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a9
- Add protocol selection to settings window

* Mon Jul 03 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a8
- Implement settings window
- Add vpn accelerator selection to setting window

* Mon Jun 19 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.0.0~a7
- VPN data refresh fix

* Tue Jun 06 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.0.0~a6
- Retrieve VPN account if it wasn't retrieved yet

* Mon May 29 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a5
- Ensure UI updates smoothly after starting with auto-connect

* Fri May 26 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a4
- Add auto-connect on app startup feature

* Thu May 25 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.0.0~a3
- Add server feature icons

* Thu May 11 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 4.0.0~a2
- Display loading widget during login/logout with a custom message

* Tue May 02 2023 Josep Llaneras <josep.llaneras@proton.ch> 4.0.0~a1
- Send app version to REST API

* Thu Apr 27 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.20.8
- Standardize how error messages are displayed

* Mon Apr 24 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.20.7
- Implement Network Manager logs

* Mon Apr 24 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.20.6
- Fix UI colors for light theme

* Fri Apr 21 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.20.5
- Allow cancelling connection/reconnection

* Fri Apr 21 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.20.4
- Update accent colours

* Wed Apr 19 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.20.3
- Update UI style on Login

* Fri Apr 14 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.20.2
- Remove IPv6 leak protection when quitting the app while in error state

* Fri Apr 14 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.20.1
- Fix reconnection after implementing IPv6 leak protection

* Tue Apr 04 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.20.0
- Use stock icon to show when a country row is expanded/collapsed

* Mon Apr 03 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.19.3
- Adapt to VPN connection refactoring

* Thu Mar 16 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.19.2
- Display last received error message via popup when multiple errors are to be displayed, instead of stacking them

* Wed Mar 15 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.19.1
- Hide secure-core servers from server list

* Wed Mar 08 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.19.0
- Remove connection and keyring backend dependencies

* Mon Mar 06 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.18.0
- Add pinned servers to tray

* Fri Mar 03 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.17.2
- Close app window safely when the "Quit" menu entry is selected

* Tue Feb 28 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.17.1
- Implement new appversion format

* Fri Feb 24 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.17.0
- Feature: Connect or disconnect from tray

* Thu Feb 23 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.16.0
- Update tray indicator icon based on vpn connection status

* Wed Feb 22 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.15.1
- Display show/hide menu entry on the tray indicator

* Mon Feb 20 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.15.0
- Use tray indicator if possible

* Wed Feb 15 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.14.0
- Feature: Add option to enter recovery code if 2fa is enabled

* Wed Feb 15 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.13.6
- Fix focus issues on login widget
- Wait that the bug report is sent before closing the window

* Tue Feb 14 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.13.5
- Fix: Logout from app if session is invalid when contacting the API

* Fri Feb 10 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.13.4
- Refactor widget package structure

* Thu Feb 09 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.13.3
- Fix crash when connected server would go into maintenance

* Wed Feb 08 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.13.2
- Fix random reconnection issues

* Tue Feb 07 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.13.1
- Fix several search issues

* Tue Feb 07 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.13.0
- Move logout to menu and refactor code

* Mon Feb 06 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.12.0
- Add search bar

* Thu Feb 02 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.11.2
- Fix app icon for Wayland

* Mon Jan 30 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.11.1
- Fix bug report dialog as per customer support guidelines

* Mon Jan 30 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.11.0
- Feature: About dialog

* Thu Jan 26 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.10.4
- Display pop-up when unable to reach API during logout

* Thu Jan 26 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.10.3
- Add window icon

* Mon Jan 23 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.10.2
- Submit bug report using proton-core

* Mon Jan 23 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.10.1
- Fix: Bug report feature

* Tue Jan 17 2023 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.10.0
- Feature: Add issue report submission dialog

* Fri Jan 13 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.9.5
- Load VPN server details from persisted connection

* Wed Jan 11 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.9.4
- Fail silently when the server list or the client config could not be updated

* Fri Jan 06 2023 Josep Llaneras <josep.llaneras@proton.ch> 0.9.3
- Fix quick connect widget glitch when opening the app twice

* Thu Dec 29 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.9.2
- Attempt to reconnect after user session has been unlocked from suspend

* Thu Dec 22 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.9.1
- Do not show popups on connection errors

* Tue Dec 20 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.9.0
- Add unit tests and improve API data handling

* Wed Dec 14 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.8.0
- Reconnect to VPN when network connectivity is detected

* Tue Dec 06 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.7.2
- Fix app crash after starting the app with a persisted connection

* Tue Dec 06 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.7.1
- Fix issue where current connection was not properly being detected

* Mon Dec 05 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.7.0
- Get server name/id from connection status update

* Fri Dec 02 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.6.6
- Ensure that UI is updated after logout/login

* Tue Nov 15 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.6.5
- Check if the current connection is active before disconnecting

* Tue Nov 15 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.6.4
- Display error dialog whenever a connection fails to be established

* Fri Nov 11 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.6.3
- Add Proton VPN logging library

* Mon Nov 07 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.6.2
- Ensure that vpn connection is stopped before logging out the user, if there is one

* Fri Nov 04 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.6.1
- Fix bug happening when connecting to a server without disconnecting first from the previous one

* Mon Oct 31 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.6.0
- Show the login screen when the session expired

* Tue Oct 04 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.5.1
- Fix several bugs in the server list widget

* Wed Sep 28 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.5.0
- Add "Connect" button on country rows

* Mon Sep 26 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.4.1
- Cleanup server list after logout

* Fri Sep 23 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.4.0
- Properly implement Quick Connect

* Fri Sep 23 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.3.1
- Fix crash when connecting to free server

* Thu Sep 22 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.3.0
- Display upgrade button for servers that require a higher tier plan to connect to

* Wed Sep 21 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.2.0
- Group servers by country

* Tue Sep 20 2022 Alexandru Cheltuitor <alexandru.cheltuitor@proton.ch> 0.1.2
- Add basic logging

* Mon Sep 19 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.1.1
- Fix app freeze when disconnecting from VPN

* Thu Sep 15 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.1.0
- Allow the user to connect to a concrete VPN server

* Wed Jun 22 2022 Josep Llaneras <josep.llaneras@proton.ch> 0.0.0
- First release

