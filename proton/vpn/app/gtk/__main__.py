"""
App entry point.
"""

import sys
from concurrent.futures import ThreadPoolExecutor

from proton.vpn.app.gtk.app import App


def main():
    """Runs the app."""

    with ThreadPoolExecutor() as thread_pool_executor:
        sys.exit(App(thread_pool_executor).run(sys.argv))


if __name__ == "__main__":
    main()
