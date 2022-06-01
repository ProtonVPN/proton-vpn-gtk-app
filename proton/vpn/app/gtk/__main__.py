import sys
import logging
from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.app import App


def main():
    logging.basicConfig(level=logging.INFO)
    with ThreadPoolExecutor() as thread_pool_executor:
        sys.exit(App(thread_pool_executor).run())


if __name__ == "__main__":
    main()
