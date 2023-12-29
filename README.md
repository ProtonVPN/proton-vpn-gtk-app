# Proton VPN GTK app

Copyright (c) 2023 Proton AG

This repository holds the Proton VPN GTK app.
For licensing information see [COPYING](COPYING.md) and [LICENSE](LICENSE).
For contribution policy see [CONTRIBUTING](CONTRIBUTING.md).

## Description

The [Proton VPN](https://protonvpn.com) GTK app is intended for every Proton VPN service user, it provides full access to all functionalities available to authenticated users, with the user signup process handled on the website.

### Installation

You can get the latest stable release from our [Proton VPN official website](https://protonvpn.com/download-linux).

### Dependencies

For development purposes (within a virtual environment) see the required packages in the setup.py file, under `install_requires` and `extra_require`. As of now these packages will not be available on pypi. Also see [Virtual environment](#virtual-environment) below.

### Virtual environment

If you didn't do it yet, to be able to pip install Proton VPN components you'll
need to set up our internal Python package registry. You can do so running the
command below, after replacing `{GITLAB_TOKEN`} with your
[personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
with the scope set to `api`.

```shell
pip config set global.index-url https://__token__:{GITLAB_TOKEN}@{GITLAB_INSTANCE}/api/v4/groups/{GROUP_ID}/-/packages/pypi/simple
```

You can create the virtual environment and install the rest of dependencies as
follows:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### GUI application

App logs are stored under `~/.cache/Proton/VPN/logs/` directory.

User settings are under `~/.config/Proton/VPN/` directory.

## Folder structure

### Folder "debian"

Contains all debian related data, for easy package compilation.

### Folder "rpmbuild"

Contains all rpm/fedora related data, for easy package compilation.

### Folder "proton/app/gtk"

This folder contains the gtk app source code.

### Folder "tests"

This folder contains unit/integrations test code.

You can run the integration tests with:

```shell
behave tests/integration/features
```

On headless systems, it's possible to run the integration tests using `Xvfb`
(virtual framebuffer X server). On Debian-based distributions, you just have
to install the `xvfb` package. After that, you can run the integration tests with:

```shell
xvfb-run -a behave integration_tests/features
```

## Versioning
Version matches format: `[major][minor][patch]`