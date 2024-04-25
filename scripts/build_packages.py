#!/usr/bin/env python
'''
This program generates a deb changelog file, and rpm spec file and a
CHANGELOG.md file for this project.

It reads versions.yml.
'''
import os
import yaml
import versions

# The root of this repo
ROOT = os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))
)

NAME      = "proton-vpn-gtk-app" # Name of this application.
VERSIONS  = os.path.join(ROOT, "versions.yml") # Name of this applications versions.yml
RPM       = os.path.join(ROOT, "rpmbuild", "SPECS", "package.spec") # Path of spec filefor rpm.
DEB       = os.path.join(ROOT, "debian", "changelog")  # Path of debian changelog.
MARKDOWN  = os.path.join(ROOT, "CHANGELOG.md",) # Path of CHANGELOG.md.

# The template for the rpm spec file.
#
SPEC_TEMPLATE='''
%define unmangled_name proton-vpn-gtk-app
%define version {version}
%define upstream_version {upstream_version}
%define logo_filename proton-vpn-logo.svg
%define desktop_entry_filename protonvpn-app.desktop
%define release 1

Prefix: %{{_prefix}}
Name: %{{unmangled_name}}
Version: %{{version}}
Release: %{{release}}%{{?dist}}
Summary: %{{unmangled_name}} library

Group: ProtonVPN
License: GPLv3
Vendor: Proton Technologies AG <opensource@proton.me>
URL: https://github.com/ProtonVPN/%{{unmangled_name}}
Source0: %{{unmangled_name}}-%{{upstream_version}}.tar.gz
Source3: %{{desktop_entry_filename}}
Source4: %{{logo_filename}}
BuildArch: noarch
BuildRoot: %{{_tmppath}}/%{{unmangled_name}}-%{{version}}-%{{release}}-buildroot

BuildRequires: gtk3
BuildRequires: desktop-file-utils
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-gobject
BuildRequires: python3-dbus
BuildRequires: python3-proton-vpn-api-core >= 0.24.0
BuildRequires: python3-proton-vpn-logger
BuildRequires: librsvg2
BuildRequires: python3-packaging

Requires: gtk3
Requires: python3-gobject
Requires: python3-dbus
Requires: python3-proton-vpn-api-core >= 0.24.0
Requires: python3-proton-vpn-logger
Requires: librsvg2
Requires: python3-packaging
Suggests: libappindicator-gtk3

%{{?python_disable_dependency_generator}}

%description
Package %{{unmangled_name}}.

%prep
%setup -n %{{unmangled_name}}-%{{upstream_version}}

%build
python3 setup.py build

%install
desktop-file-install --dir=%{{buildroot}}%{{_datadir}}/applications %{{SOURCE3}}
desktop-file-validate %{{buildroot}}%{{_datadir}}/applications/%{{desktop_entry_filename}}
mkdir -p %{{buildroot}}%{{_datadir}}/icons/hicolor/scalable/apps
cp %{{SOURCE4}} %{{buildroot}}%{{_datadir}}/icons/hicolor/scalable/apps/%{{logo_filename}}
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%files -f INSTALLED_FILES
%{{python3_sitelib}}/proton/
%{{python3_sitelib}}/proton_vpn_gtk_app-%{{upstream_version}}*.egg-info/
%{{_datadir}}/applications/%{{desktop_entry_filename}}
%{{_datadir}}/icons/hicolor/scalable/apps/%{{logo_filename}}
%defattr(-,root,root)

%changelog'''

def build():
    '''
    This is what generates the rpm spec, deb changelog and
    markdown CHANGELOG.md file.
    '''
    with open(VERSIONS, encoding="utf-8") as versions_file:

        # Load versions.yml
        versions_yml = list(yaml.safe_load_all(versions_file))

        # Make our files
        versions.build_rpm(RPM,      versions_yml, SPEC_TEMPLATE)
        versions.build_deb(DEB,      versions_yml, NAME)
        versions.build_mkd(MARKDOWN, versions_yml)

if __name__ == "__main__":
    build()
