"""
Server list is retrieved from a local web server using aiohttp
every second. The scheduler IS used.

Memory leak WAS DETECTED.
"""
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

import aiohttp
from gi.repository import GLib

from proton.vpn.session import ServerList

from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from proton.vpn.app.gtk.utils.scheduler2 import Scheduler

SERVER_LIST_URL = "http://localhost:8000/serverlist.json"

scheduler = Scheduler(check_interval_in_ms=100)
server_list: ServerList = None
read_counter = 0
executor = AsyncExecutor()

def run_http_server():
    print("Starting HTTP server...")
    server_address = ('127.0.0.1', 8000)
    http_server = HTTPServer(server_address, SimpleHTTPRequestHandler)
    threading.Thread(target=http_server.serve_forever, daemon=True).start()
    time.sleep(1)

async def get_server_list_async():
    global read_counter
    print(f"Getting server list... (# {read_counter})")
    global server_list
    async with aiohttp.ClientSession() as session:
        async with session.get(SERVER_LIST_URL) as response:
            server_list = ServerList.from_dict(await response.json())
    print("Server list read.")
    read_counter += 1

def get_server_list():
    future = executor.submit(get_server_list_async)
    future.add_done_callback(lambda f: GLib.idle_add(f.result))

def get_server_list_periodically():
    scheduler.run_after(task=get_server_list, delay_in_seconds=1)
    return GLib.SOURCE_CONTINUE


def run_test():
    scheduler.start()
    executor.start()
    run_http_server()
    GLib.timeout_add(1000, get_server_list_periodically)
    # scheduler.run_after(task=get_server_list, delay_in_seconds=0)


if __name__ == "__main__":
    run_test()
    GLib.MainLoop().run()
