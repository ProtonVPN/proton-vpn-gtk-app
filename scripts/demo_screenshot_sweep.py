#!/usr/bin/env python3
"""
Demo screenshot sweep — capture every registered demo screen under every
GTK4 theme in the distro reference matrix.

Default sweep (no --theme):
  Each unique theme is rendered once and copied to each distro subdirectory
  that uses it.
  Output: <output>/<screen>/<distro>-<version>/<screen>__<theme>.png

Manual sweep (--theme):
  Captures only the specified themes. No distro context; flat output.
  Output: <output>/<screen>/<screen>__<theme>.png

Usage:
    scripts/demo_screenshot_sweep.py [--theme THEME ...] [--screen SCREEN ...]
                                      [--output DIR] [--list-themes]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404  # nosemgrep: gitlab.bandit.B404
import sys
from pathlib import Path

# Each distro/version entry lists ALL GTK4 base themes for that environment:
# light, dark, high-contrast light, high-contrast dark.
#
# GTK4 built-ins (Default*) are compiled into libgtk-4 — no package needed.
# Yaru requires: yaru-theme-gtk (Debian/Ubuntu), yaru-gtk4-theme (Fedora).
#
# Distro           Version   Themes
# ──────────────── ─────────  ──────────────────────────────────────────────────
# Fedora           43, 44     Default  Default-dark  Default-hc  Default-hc-dark
# Ubuntu           24.04 LTS  Yaru     Yaru-dark     Default-hc  Default-hc-dark
# Ubuntu           26.04 LTS  Yaru     Yaru-dark     Default-hc  Default-hc-dark
# Debian           12, 13     Default  Default-dark  Default-hc  Default-hc-dark
_DISTRO_THEMES: dict[tuple[str, str], list[str]] = {
    ("fedora",  "43"):   ["Default", "Default-dark", "Default-hc", "Default-hc-dark"],
    ("fedora",  "44"):   ["Default", "Default-dark", "Default-hc", "Default-hc-dark"],
    ("ubuntu", "24.04"): ["Yaru",    "Yaru-dark",    "Default-hc", "Default-hc-dark"],
    ("ubuntu", "26.04"): ["Yaru",    "Yaru-dark",    "Default-hc", "Default-hc-dark"],
    ("debian",  "12"):   ["Default", "Default-dark", "Default-hc", "Default-hc-dark"],
    ("debian",  "13"):   ["Default", "Default-dark", "Default-hc", "Default-hc-dark"],
}

# GTK4 built-in themes — compiled into libgtk-4, never requires on-disk files.
_GTK4_BUILTINS: frozenset[str] = frozenset({
    "Default", "Default-dark", "Default-hc", "Default-hc-dark",
})

# Standard XDG theme search roots, highest priority first.
_THEME_ROOTS: list[Path] = [
    Path.home() / ".local/share/themes",
    Path.home() / ".themes",
    Path("/usr/local/share/themes"),
    Path("/usr/share/themes"),
]

# The demo app is a standalone entry point.
_DEMO_CMD: list[str] = [sys.executable, "-m", "proton.vpn.app.gtk.demo"]


def _find_installed_gtk4_dir(name: str) -> Path | None:
    for root in _THEME_ROOTS:
        candidate = root / name / "gtk-4.0"
        if candidate.is_dir():
            return candidate
    return None


def _theme_name(name_or_path: str) -> str:
    """Theme name used in filenames: basename for paths, name as-is for named themes."""
    p = Path(name_or_path)
    return p.name if (p.is_absolute() or len(p.parts) > 1) else name_or_path


def _distro_dir(
    distro: str,
    ver: str,
) -> str:
    return f"{distro}-{ver}"


def _validate_theme(name_or_path: str) -> bool:
    """True if the theme has GTK4 support or is a GTK4 built-in."""
    if name_or_path in _GTK4_BUILTINS:
        return True
    p = Path(name_or_path)
    if p.is_absolute() or len(p.parts) > 1:
        return (p / "gtk-4.0").is_dir()
    return _find_installed_gtk4_dir(name_or_path) is not None


def _theme_env(name_or_path: str) -> dict[str, str]:
    """Return the env vars needed to activate this theme in a subprocess."""
    p = Path(name_or_path)
    if p.is_absolute() or len(p.parts) > 1:
        # Path given directly: prepend the parent to XDG_DATA_DIRS so GTK
        # finds the theme by its basename.
        existing = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        return {
            "XDG_DATA_DIRS": f"{p.parent}:{existing}",
            "GTK_THEME": p.name,
        }
    return {"GTK_THEME": name_or_path}


def _list_installed_gtk4_themes() -> list[str]:
    """All theme names with gtk-4.0 support found in standard search roots."""
    found: dict[str, None] = {}  # ordered set; higher-priority roots win
    for root in reversed(_THEME_ROOTS):
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and (entry / "gtk-4.0").is_dir():
                found[entry.name] = None
    return list(found)


def _get_screen_names(cmd: list[str]) -> list[str]:
    """Ask the demo app for its registered demo screen names."""
    try:
        result = subprocess.run(  # nosec B603  # noqa: E501  # pylint: disable=line-too-long  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
            cmd + ["--demo-list"],
            capture_output=True, text=True, check=True,
        )
        return [s.strip() for s in result.stdout.splitlines() if s.strip()]
    except subprocess.CalledProcessError as exc:
        sys.exit(f"error: failed to list demo screens: {exc.stderr.strip()}")


def _capture(
    cmd: list[str],
    screen: str,
    theme: str,
    out: Path,
) -> bool:
    """Run one screenshot capture. Returns True on success."""
    out.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **_theme_env(theme)}
    try:
        result = subprocess.run(  # nosec B603  # noqa: E501  # pylint: disable=line-too-long  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
            cmd + [f"--demo={screen}", f"--screenshot={out}"],
            env=env,
            timeout=30,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.TimeoutExpired:
        print("    warning: timed out after 30 s", file=sys.stderr)
        return False

    if result.returncode != 0:
        print(
            f"    warning: app exited with code {result.returncode}",
            file=sys.stderr,
        )
        if result.stderr:
            for line in result.stderr.splitlines():
                print(f"    {line}", file=sys.stderr)
        return False

    if not out.is_file():
        print(
            f"    warning: app exited cleanly but {out} was not written",
            file=sys.stderr,
        )
        return False

    return True


def _run_matrix_sweep(
    cmd: list[str],
    screens: list[str],
    output_root: Path,
) -> tuple[int, int]:
    """Default distro matrix sweep.

    Builds a theme → [distro_dir, ...] map so each unique theme is rendered
    exactly once, then copied to every other distro directory that shares it.
    """
    # theme → ordered list of distro dirs that use it (first dir = capture target)
    theme_to_dirs: dict[str, list[str]] = {}
    for (distro, ver), themes in _DISTRO_THEMES.items():
        dir_name = _distro_dir(distro, ver)
        for theme in themes:
            if theme not in theme_to_dirs:
                theme_to_dirs[theme] = []
            if dir_name not in theme_to_dirs[theme]:
                theme_to_dirs[theme].append(dir_name)

    # Validate upfront; drop unavailable themes with a warning.
    valid_themes: dict[str, list[str]] = {}
    for theme, dir_names in theme_to_dirs.items():
        if _validate_theme(theme):
            valid_themes[theme] = dir_names
        else:
            print(
                f"warning: skipping {theme!r} — not found or GTK3-only "
                f"(would silently fall back to Default)",
                file=sys.stderr,
            )

    if not valid_themes:
        sys.exit("error: no valid themes to sweep")

    n_unique = len(valid_themes)
    n_files = sum(len(screens) * len(dir_names) for dir_names in valid_themes.values())
    print(
        f"Sweeping {len(screens)} screen(s) × {n_unique} unique theme(s) "
        f"= {len(screens) * n_unique} renders, {n_files} output files\n"
        f"Output → {output_root.resolve()}\n"
    )

    done = 0
    failed = 0

    for screen in screens:
        for theme, dir_names in valid_themes.items():
            name = _theme_name(theme)
            primary = output_root / screen / dir_names[0] / f"{screen}__{name}.png"
            copies = [
                output_root / screen / s / f"{screen}__{name}.png"
                for s in dir_names[1:]
            ]
            copy_note = f"  → copy to {', '.join(dir_names[1:])}" if copies else ""
            print(f"  {screen} / {theme}  [{dir_names[0]}]{copy_note}")
            if _capture(cmd, screen, theme, primary):
                done += 1
                for dest in copies:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(primary, dest)
            else:
                failed += 1

    return done, failed


def _run_manual_sweep(
    cmd: list[str],
    screens: list[str],
    themes: list[str],
    output_root: Path,
) -> tuple[int, int]:
    """Manual --theme sweep: flat output, no distro subdirectory."""
    total = len(screens) * len(themes)
    print(
        f"Sweeping {len(screens)} screen(s) × {len(themes)} theme(s) "
        f"= {total} captures\n"
        f"Output → {output_root.resolve()}\n"
    )

    done = 0
    failed = 0

    for screen in screens:
        for theme in themes:
            name = _theme_name(theme)
            out = output_root / screen / f"{screen}__{name}.png"
            print(f"  {screen} / {name}")
            if _capture(cmd, screen, theme, out):
                done += 1
            else:
                failed += 1

    return done, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Capture each demo screen under each GTK theme used by a supported distro. "
            "Output: <output>/<screen>/<distro>-<ver>/<screen>__<theme>.png"
        )
    )
    parser.add_argument(
        "--list-themes", action="store_true",
        help="Show the per-distro theme list and installed themes, then exit.",
    )
    parser.add_argument(
        "--theme", action="append", dest="themes", metavar="THEME",
        help=(
            "Theme name or path (repeatable). Bypasses the per-distro theme list; "
            "output goes to <output>/<screen>/<screen>__<theme>.png (no distro subdir)."
        ),
    )
    parser.add_argument(
        "--screen", action="append", dest="screens", metavar="SCREEN",
        help="Demo screen to capture (repeatable). Default: all registered screens.",
    )
    parser.add_argument(
        "--output", default="./screenshots", metavar="DIR",
        help="Output root directory (default: ./screenshots).",
    )
    args = parser.parse_args()

    if args.list_themes:
        installed = set(_list_installed_gtk4_themes())
        all_matrix_themes: set[str] = set()
        for themes in _DISTRO_THEMES.values():
            all_matrix_themes.update(themes)

        print("Distro theme matrix:")
        for (distro, ver), themes in _DISTRO_THEMES.items():
            dir_name = _distro_dir(distro, ver)
            entries = [
                f"{t} [{'ok' if _validate_theme(t) else 'NOT INSTALLED'}]"
                for t in themes
            ]
            print(f"  {dir_name:16s}  {',  '.join(entries)}")

        extra = sorted(installed - all_matrix_themes)
        if extra:
            print("\nOther installed GTK4 themes:")
            for name in extra:
                print(f"  {name}")
        return

    screens: list[str] = args.screens or _get_screen_names(_DEMO_CMD)
    if not screens:
        sys.exit("error: no demo screens found")

    if args.themes:
        valid: list[str] = []
        for t in args.themes:
            if _validate_theme(t):
                valid.append(t)
            else:
                print(
                    f"warning: skipping {t!r} — not found or GTK3-only "
                    f"(would silently fall back to Default)",
                    file=sys.stderr,
                )
        if not valid:
            sys.exit("error: no valid themes to sweep")
        done, failed = _run_manual_sweep(_DEMO_CMD, screens, valid, Path(args.output))
    else:
        done, failed = _run_matrix_sweep(_DEMO_CMD, screens, Path(args.output))

    total = done + failed
    print(f"\n{done}/{total} renders written", end="")
    if failed:
        print(f", {failed} failed", end="")
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
