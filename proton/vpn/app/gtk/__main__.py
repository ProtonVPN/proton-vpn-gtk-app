"""
App entry point.
"""

import sys
import logging
from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.app import App


def main():
    """Runs the app."""
    logging.basicConfig(level=logging.INFO)

    with ThreadPoolExecutor() as thread_pool_executor:
        sys.exit(App(thread_pool_executor).run(sys.argv))


if __name__ == "__main__":
    main()
