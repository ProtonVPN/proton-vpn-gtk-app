#!/usr/bin/env python

from setuptools import setup, find_namespace_packages
from setuptools.command.build_py import build_py
import os
import re
import subprocess  # nosec B404  # nosemgrep: gitlab.bandit.B404

VERSIONS = 'versions.yml'
VERSION = re.search(r'version: (\S+)', open(VERSIONS, encoding='utf-8')
                    .readline()).group(1)

DOMAIN = "proton-vpn-gtk-app"
PO_DIR = "proton/vpn/app/gtk/locale"


class BuildPyWithTranslations(build_py):
    """Compile .po to .mo."""
    def run(self):
        super().run()
        po_files = sorted(
            f for f in os.listdir(PO_DIR) if f.endswith(".po")
        ) if os.path.isdir(PO_DIR) else []
        if not po_files:
            raise FileNotFoundError(
                f"No .po files found in {PO_DIR}; cannot build translations.")
        for po in po_files:
            out_dir = os.path.join(
                self.build_lib, PO_DIR, "binaries", po[:-3], "LC_MESSAGES")
            os.makedirs(out_dir, exist_ok=True)
            subprocess.run(  # nosec  # nosemgrep: gitlab.bandit.B603
                ["msgfmt", "-c", "-o",
                 os.path.join(out_dir, f"{DOMAIN}.mo"),
                 os.path.join(PO_DIR, po)],
                check=True)


setup(
    name="proton-vpn-gtk-app",
    version=VERSION,
    description="Proton VPN GTK app",
    author="Proton AG",
    author_email="opensource@proton.me",
    url="https://github.com/ProtonVPN/proton-vpn-gtk-app",
    install_requires=[
        "proton-vpn-api-core",
        "pygobject",
        "pycairo",
        "dbus-python",
        "packaging",
        "distro",
        "requests",
        "proton-core"
    ],
    extras_require={
        "development": [
            "proton-keyring-linux",
            "behave",
            "pyotp",
            "pytest",
            "pytest-cov",
            "pytest-xvfb",
            "pygobject-stubs",
            "flake8",
            "pylint",
            "mypy",
            "PyYAML"
        ]
    },
    packages=find_namespace_packages(
        include=["proton.vpn.app.*"],
        # The demo package is a development-only tool
        exclude=["proton.vpn.app.gtk.demo", "proton.vpn.app.gtk.demo.*"],
    ),
    include_package_data=True,
    cmdclass={"build_py": BuildPyWithTranslations},
    python_requires=">=3.9",
    license="GPLv3",
    platforms="Linux",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Security",
    ],
    entry_points={
        "console_scripts": [
            ['protonvpn-app=proton.vpn.app.gtk.__main__:main'],
        ],
    }
)
