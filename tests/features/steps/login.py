import os
import threading

from proton.sso import ProtonSSO

from behave import given, when, then


os.environ["PROTON_API_ENVIRONMENT"] = "atlas"
USERNAME = "vpnplus"
PASSWORD = "12341234"


@given("the user is not logged in")
def step_impl(context):
    session = ProtonSSO().get_session(account_name=USERNAME)
    if session.authenticated:
        session.logout()


@when("a correct username and password is submitted")
def step_impl(context):
    app = context.app

    # Register callback to be notified once the user is logged in.
    context.user_logged_in = threading.Event()
    def on_user_logged_in(_):  # noqa E306.
        context.user_logged_in.set()
    app.window.login_widget.connect("user-logged-in", on_user_logged_in)

    login_form = app.window.login_widget.login_form

    login_form.username = USERNAME
    login_form.password = PASSWORD
    login_form.submit_login()


@then("the user should be logged in.")
def step_impl(context):
    # Wait for the user-logged-in event.
    user_logged_in = context.user_logged_in.wait(timeout=10)
    assert user_logged_in

    session = ProtonSSO().get_session(account_name=USERNAME)
    assert session.authenticated
