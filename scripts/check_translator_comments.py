#!/usr/bin/env python3
"""
Fail the build if any translatable string lacks a translator comment (#.).
"""
import sys

DEFAULT_POT = "po/proton-vpn-gtk-app.pot"


def undocumented(path):
    """
    Return .pot entries that have a msgid but no translator comment.
    Skips header and obsolete entries (#~).
    :param path: path to the .pot/.po file.
    :return: list of entries without translator comment.
    """
    with open(path, encoding="utf-8") as pot_file:
        blocks = pot_file.read().split("\n\n")
    bad = []
    for block in blocks[1:]:                       # [0] is the header
        lines = block.splitlines()
        obsolete = any(line.startswith("#~") for line in lines)
        has_msgid = any(line.startswith("msgid ") for line in lines)
        if obsolete or not has_msgid:
            continue
        if not any(line.startswith("#.") for line in lines):
            bad.append(block.strip())
    return bad


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_POT
    bad = undocumented(path)
    for block in bad:
        print(block, end="\n\n")
    if bad:
        print(f"{len(bad)} string(s) missing a translator comment in {path}.", file=sys.stderr)
        return 1
    print(f"All translatable strings in {path} have a comment.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
