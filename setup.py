#!/usr/bin/env python

from setuptools import setup, find_namespace_packages
import re

VERSIONS = 'versions.yml'
VERSION = re.search(r'version: (\S+)', open(VERSIONS, encoding='utf-8')
                    .readline()).group(1)

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
            "proton-core-internal",
            "proton-keyring-linux",
            "proton-vpn-network-manager",
            "proton-vpn-local-agent",
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
