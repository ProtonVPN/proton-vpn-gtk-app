"""
Fixtures and steps for the Server List feature.


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
from behave import given, when, then, fixture, use_fixture

from proton.vpn.core.api import ProtonVPNAPI
from proton.vpn.core.session import ClientTypeMetadata


def before_feature_serverlist(context, feature):
    """Called before running the tests for the Server List feature from
    environment.py."""
    use_fixture(logged_in_session, context)


@fixture
def logged_in_session(context):
    context.api = ProtonVPNAPI(ClientTypeMetadata("gui", "4.0.0"))
    result = context.api.login(username=context.free_user_name, password=context.free_user_password)
    assert result.success, f"Unable to login with {context.free_user_name}."
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
    assert len([server_row for country_row in servers_widget.country_rows for server_row in country_row]) > 0
