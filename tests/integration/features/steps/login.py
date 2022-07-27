import os
import threading

from proton.sso import ProtonSSO
import subprocess
from keyring.backends import SecretService
from behave import given, when, then
import pyotp


os.environ["PROTON_API_ENVIRONMENT"] = "atlas"
VPNPLUS_USERNAME = "vpnplus"
VPNPLUS_PASSWORD = "12341234"


@given("a user without 2FA enabled")
def step_impl(context):
    context.username = VPNPLUS_USERNAME
    context.password = VPNPLUS_PASSWORD


@given("the user is not logged in")
def step_impl(context):
    if not hasattr(context, "username"):
        # Default to vpnplus user.
        context.username = VPNPLUS_USERNAME
        context.password = VPNPLUS_PASSWORD

    session = ProtonSSO().get_session(account_name=context.username)
    if session.authenticated:
        session.logout()


@when("the correct username and password are introduced in the login form")
def step_impl(context):
    login_form = context.app.window.main_widget.login_widget.login_form
    login_form.username = context.username
    login_form.password = context.password


@when("the wrong password is introduced")
def step_impl(context):
    login_form = context.app.window.main_widget.login_widget.login_form
    login_form.username = context.username
    login_form.password = "wrong password"


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

    # Notify when a login error occurred.
    context.login_error_event = threading.Event()
    context.login_error_occurred = False
    def on_login_error(_):  # noqa: E306
        context.login_error_occurred = True
        context.login_error_event.set()
    login_form.connect("login-error", on_login_error)

    # Notify when the user is logged in.
    context.user_logged_in_event = threading.Event()
    login_widget.connect(
        "user-logged-in",
        lambda _: context.user_logged_in_event.set()
    )

    login_form.submit_login()


@when("the login data is not provided")
def step_impl(context):
    login_form = context.app.window.main_widget.login_widget.login_form
    login_form.username = ""
    login_form.password = context.password


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


@given("keyring is unlocked")
def step_impl(context):
    # Unlock keyring
    start_keyring_process = subprocess.Popen(
        "gnome-keyring-daemon --unlock",
        stdin=subprocess.PIPE,
        shell=True
    )
    stdout, stderr = start_keyring_process.communicate(b"printf '\n'\n")
    assert start_keyring_process.returncode == 0


@then("the credentials are stored in the system's keyring")
def step_impl(context):
    # Wait for the user-logged-in event.

    user_logged_in = context.user_logged_in_event.wait(timeout=10)
    assert user_logged_in

    backend = SecretService.Keyring()
    assert context.username in backend.get_password("Proton", "proton-sso-accounts")


@given("a user with 2FA enabled")
def step_impl(context):
    context.username = "twofa"
    context.password = "a"
    context.two_factor_auth_shared_secret = "4R5YJICSS6N72KNN3YRTEGLJCEKIMSKJ"


@when("a correct 2FA code is submitted")
def step_impl(context):
    # Wait for the user to be authenticated before submitting the 2FA code
    user_authenticated = context.user_authenticated_event.wait(timeout=10)
    assert user_authenticated

    assert context.two_factor_auth_required

    two_factor_auth_form = context.app.window.main_widget.login_widget.two_factor_auth_form
    two_factor_auth_form.two_factor_auth_code = pyotp.TOTP(
        context.two_factor_auth_shared_secret
    ).now()
    two_factor_auth_form.submit_two_factor_auth()


@then('the user should be notified with the error message: "{error_message}"')
def step_impl(context, error_message):
    assert context.login_error_event.wait(timeout=10)

    assert context.login_error_occurred

    login_form = context.app.window.main_widget.login_widget.login_form
    assert error_message == login_form.error_message
