import sys
import logging

from proton.vpn.app.gtk.gui import GUI


def main():
    logging.basicConfig(level=logging.INFO)
    sys.exit(GUI().show())


if __name__ == "__main__":
    main()
