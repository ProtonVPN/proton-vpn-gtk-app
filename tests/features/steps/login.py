import os
import threading

from proton.sso import ProtonSSO

from behave import given, when, then
import pyotp


os.environ["PROTON_API_ENVIRONMENT"] = "atlas"


@given("a user without 2FA enabled")
def step_impl(context):
    context.username = "vpnplus"
    context.password = "12341234"


@given("the user is not logged in")
def step_impl(context):
    session = ProtonSSO().get_session(account_name=context.username)
    if session.authenticated:
        session.logout()


@when("a correct username and password is submitted")
def step_impl(context):
    login_widget = context.app.window.login_widget
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

    login_form.username = context.username
    login_form.password = context.password
    login_form.submit_login()


@then("the user should be logged in.")
def step_impl(context):
    # Wait for the user-logged-in event.
    user_logged_in = context.user_logged_in_event.wait(timeout=10)
    assert user_logged_in

    session = ProtonSSO().get_session(account_name=context.username)
    assert session.authenticated


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

    two_factor_auth_form = context.app.window.login_widget.two_factor_auth_form
    two_factor_auth_form.two_factor_auth_code = pyotp.TOTP(
        context.two_factor_auth_shared_secret
    ).now()
    two_factor_auth_form.submit_two_factor_auth()
