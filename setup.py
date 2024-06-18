#!/usr/bin/env python

from setuptools import setup, find_namespace_packages
import re

VERSIONS = 'versions.yml'
VERSION = re.search(r'version: (\S+)', open(VERSIONS).readline()).group(1)

setup(
    name="proton-vpn-gtk-app",
    version=VERSION,
    description="Proton VPN GTK app",
    author="Proton AG",
    author_email="contact@protonmail.com",
    url="https://github.com/ProtonVPN/proton-vpn-gtk-app",
    install_requires=[
        "proton-vpn-api-core",
        "proton-vpn-logger",
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
            "proton-core-internal",
            "proton-keyring-linux-secretservice",
            "proton-vpn-network-manager-openvpn",
            "proton-vpn-killswitch-network-manager",
            "proton-vpn-network-manager-wireguard",
            "proton-vpn-killswitch-network-manager-wireguard",
            "behave",
            "pyotp",
            "pytest",
            "pytest-cov",
            "pygobject-stubs",
            "flake8",
            "pylint",
            "mypy",
            "PyYAML"
        ]
    },
    packages=find_namespace_packages(include=["proton.vpn.app.*"]),
    include_package_data=True,
    python_requires=">=3.8",
    license="GPLv3",
    platforms="OS Independent",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
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
