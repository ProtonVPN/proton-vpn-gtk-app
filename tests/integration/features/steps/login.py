"""
Fixtures and steps for the Login feature.


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
import threading

from gi.repository import GLib
from keyring.backends import SecretService
from behave import given, when, then
import pyotp

from proton.sso import ProtonSSO
from proton.vpn.core.api import ProtonVPNAPI
from proton.vpn.core.session import ClientTypeMetadata


def before_login_scenario(context, scenario):
    """Called before every login scenario from environment.py."""
    if not hasattr(context, "username"):
        # Default to vpnfree user.
        context.username = context.free_user_name
        context.password = context.free_user_password


def set_username_password_threadsafe(login_form, username, password):
    """Sets the username and password form fields in a thread-safe manner."""
    def set_username_and_password():
        login_form.username = username
        login_form.password = password

    GLib.idle_add(set_username_and_password)


def submit_2fa_code_threadsafe(two_factor_auth_form, two_factor_auth_code):
    """Sets the 2FA code form field and submits it in a thread-safe manner."""
    def set_2fa_code():
        two_factor_auth_form.two_factor_auth_code = two_factor_auth_code

    GLib.idle_add(set_2fa_code)
    GLib.idle_add(two_factor_auth_form.submit_two_factor_auth)


def after_login_scenario(context, scenario):
    """Called after every login scenario from environment.py"""
    ProtonVPNAPI(ClientTypeMetadata("gui", "4.0.0")).logout()


@given("a user without 2FA enabled")
def step_impl(context):
    context.username = context.free_user_name
    context.password = context.free_user_password


@given("the user is not logged in")
def step_impl(context):
    # Log out from any existing authenticated sessions.
    sso = ProtonSSO()
    authenticated_sessions = True
    while authenticated_sessions:
        s = sso.get_default_session()
        if s.authenticated:
            s.logout()
        else:
            authenticated_sessions = False


@when("the correct username and password are introduced in the login form")
def step_impl(context):
    login_form = context.app.window.main_widget.login_widget.login_form
    set_username_password_threadsafe(
        login_form=login_form,
        username=context.username,
        password=context.password
    )


@when("the login form is submitted")
def step_impl(context):
    login_widget = context.app.window.main_widget.login_widget
    login_form = login_widget.login_form

    # Notify when the user is authenticated.
    context.user_authenticated_event = threading.Event()
    def on_user_authenticated(_, two_factor_auth_required):  # noqa: E306
        context.two_factor_auth_required = two_factor_auth_required
        context.user_authenticated_event.set()
    login_form.connect("user_authenticated", on_user_authenticated)


    # Notify when the user is logged in.
    context.user_logged_in_event = threading.Event()
    login_widget.connect(
        "user-logged-in",
        lambda _: context.user_logged_in_event.set()
    )

    GLib.idle_add(login_form.submit_login)


@when("the login data is not provided")
def step_impl(context):
    login_form = context.app.window.main_widget.login_widget.login_form
    set_username_password_threadsafe(
        login_form=login_form,
        username="",
        password=context.password
    )


@then("the user should be logged in")
def step_impl(context):
    # Wait for the user-logged-in event.
    user_logged_in = context.user_logged_in_event.wait(timeout=10)
    assert user_logged_in

    session = ProtonSSO().get_session(account_name=context.username)
    assert session.authenticated


@then("the user should not be able to submit the form")
def step_impl(context):
    login_form = context.app.window.main_widget.login_widget.login_form
    assert login_form.is_login_button_clickable is False


@then("the credentials should be stored in the system's keyring")
def step_impl(context):
    # Wait for the user-logged-in event.

    user_logged_in = context.user_logged_in_event.wait(timeout=10)
    assert user_logged_in

    backend = SecretService.Keyring()
    assert context.username in backend.get_password("Proton", "proton-sso-accounts")


@given("a user with 2FA enabled")
def step_impl(context):
    context.username = context.two_factor_user_name
    context.password = context.two_factor_user_password
    context.two_factor_auth_shared_secret = context.two_factor_user_2fa_secret


@when("a correct 2FA code is submitted")
def step_impl(context):
    # Wait for the user to be authenticated before submitting the 2FA code
    user_authenticated = context.user_authenticated_event.wait(timeout=10)
    assert user_authenticated

    assert context.two_factor_auth_required

    two_factor_auth_form = context.app.window.main_widget.login_widget.two_factor_auth_form
    two_factor_auth_code = pyotp.TOTP(context.two_factor_auth_shared_secret).now()
    submit_2fa_code_threadsafe(two_factor_auth_form, two_factor_auth_code)
