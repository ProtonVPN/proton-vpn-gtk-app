"""
Server list is parsed from a file every second. The scheduler IS used.

Memory leak was NOT detected.
"""
import asyncio
from pathlib import Path
import json

from gi.repository import GLib

from proton.vpn.session import ServerList

from proton.vpn.app.gtk.utils.executor import AsyncExecutor
from proton.vpn.app.gtk.utils.scheduler import Scheduler

SERVER_LIST_FILE_PATH = Path(__file__).parent / "serverlist.json"

scheduler = Scheduler(check_interval_in_ms=1000)
server_list: ServerList = None
read_counter = 0
executor = AsyncExecutor()


def parse_server_list_from_file():
    with open(SERVER_LIST_FILE_PATH) as f:
        json_content = json.load(f)
    return ServerList.from_dict(json_content)

async def get_server_list_async():
    global read_counter
    print(f"Reading server list... (# {read_counter})")
    loop = asyncio.get_running_loop()
    global server_list
    server_list = await loop.run_in_executor(None, parse_server_list_from_file)
    print("Server list read.")
    read_counter += 1
    scheduler.run_after(task=get_server_list, delay_in_seconds=1)

def get_server_list():
    future = executor.submit(get_server_list_async)
    future.add_done_callback(lambda f: GLib.idle_add(f.result))

def run_test():
    scheduler.start()
    executor.start()
    scheduler.run_after(task=get_server_list, delay_in_seconds=0)


if __name__ == "__main__":
    run_test()
    GLib.MainLoop().run()
