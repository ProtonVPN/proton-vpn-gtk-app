from behave import given, then


@given("the user is logged in")
def step_impl(context):
    assert context.api.is_user_logged_in()


@given("the server list widget is ready")
def step_impl(context):
    server_list_ready = context.app_events["server-list-ready"].wait(timeout=10)
    assert server_list_ready


@then("the server list should be displayed")
def step_impl(context):
    servers_widget = context.app.window.main_widget.vpn_widget.servers_widget
    assert len(servers_widget.server_rows) > 0

