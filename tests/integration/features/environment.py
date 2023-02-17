"""
Contains the hook functions that behave runs.


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

import logging

from tests.integration.features.fixtures import before_each_scenario, create_atlas_users, delete_atlas_users, \
    configure_atlas_environment
from tests.integration.features.steps.login import before_login_scenario, \
    after_login_scenario
from tests.integration.features.steps.serverlist import before_feature_serverlist

logging.basicConfig(level=logging.INFO)


def before_all(context):
    """Hook that behave runs before all tests."""
    configure_atlas_environment()
    create_atlas_users(context)


def after_all(context):
    """Hook that behave runs after all tests."""
    delete_atlas_users(context)


def before_feature(context, feature):
    """Hook that behave runs before each feature."""
    if "not_implemented" in feature.tags:
        feature.skip("Marked with @not_implemented")
        return

    if feature.name == "Server List":
        before_feature_serverlist(context, feature)


def after_feature(context, feature):
    """Hook that behave runs after each feature."""


def before_scenario(context, scenario):
    """Hook that behave runs before each scenario."""
    if "not_implemented" in scenario.effective_tags:
        scenario.skip("Marked with @not_implemented")
        return

    # Do common things to all scenarios.
    before_each_scenario(context, scenario)

    if scenario.feature.name == "Login":
        before_login_scenario(context, scenario)


def after_scenario(context, scenario):
    """Hook that behave runs after each scenario."""
    if scenario.feature.name == "Login":
        after_login_scenario(context, scenario)
