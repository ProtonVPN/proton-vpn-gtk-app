from behave import given, when, then


@given("the user is logged in")
def step_impl(context):
    assert context.api.is_user_logged_in()


@when("the server list widget is initialized")
def step_impl(context):
    server_list_updated = context.app_events["server-list-updated"].wait(timeout=10)
    assert server_list_updated


@then("the server list should be displayed")
def step_impl(context):
    servers_widget = context.app.window.main_widget.vpn_widget.servers_widget
    assert len(servers_widget.server_rows) > 0
