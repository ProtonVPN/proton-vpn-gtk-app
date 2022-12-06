"""
Contains the hook functions that behave runs.
"""

import logging
import os

from tests.integration.features.fixtures import before_each_scenario
from tests.integration.features.steps.login import before_login_scenario, \
    after_login_scenario
from tests.integration.features.steps.serverlist import before_feature_serverlist

logging.basicConfig(level=logging.INFO)

os.environ["PROTON_API_ENVIRONMENT"] = "atlas"


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
