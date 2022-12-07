"""
Fixtures and steps for the Server List feature.
"""
from behave import given, when, then, fixture, use_fixture

from proton.vpn.core_api.api import ProtonVPNAPI

from tests.integration.features.steps.login import VPNPLUS_USERNAME, VPNPLUS_PASSWORD


def before_feature_serverlist(context, feature):
    """Called before running the tests for the Server List feature from
    environment.py."""
    use_fixture(logged_in_session, context)


@fixture
def logged_in_session(context):
    context.api = ProtonVPNAPI()
    result = context.api.login(username=VPNPLUS_USERNAME, password=VPNPLUS_PASSWORD)
    assert result.success, f"Unable to login with {VPNPLUS_USERNAME}."
    yield context.api
    context.api.logout()


@given("the user is logged in")
def step_impl(context):
    assert context.api.is_user_logged_in()


@when("the server list widget is initialized")
def step_impl(context):
    server_list_updated = context.app_events["vpn-widget-ready"].wait(timeout=10)
    assert server_list_updated


@then("the server list should be displayed")
def step_impl(context):
    servers_widget = context.app.window.main_widget.vpn_widget.server_list_widget
    assert len(servers_widget.country_rows) > 0
    assert len(servers_widget.country_rows[0].server_rows) > 0
