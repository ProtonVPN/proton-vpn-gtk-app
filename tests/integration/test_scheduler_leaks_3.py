"""
Server list is retrieved from a local web server using aiohttp
every second. The scheduler is NOT used.

NO memory leak was detected.
"""
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

import aiohttp
from gi.repository import GLib

from proton.vpn.session import ServerList

from proton.vpn.app.gtk.utils.executor import AsyncExecutor

SERVER_LIST_URL = "http://localhost:8000/serverlist.json"

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
    GLib.timeout_add(function=get_server_list, interval=1000)

def get_server_list():
    future = executor.submit(get_server_list_async)
    future.add_done_callback(lambda f: GLib.idle_add(f.result))

def run_test():
    executor.start()
    run_http_server()
    GLib.idle_add(get_server_list)


if __name__ == "__main__":
    run_test()
    GLib.MainLoop().run()
