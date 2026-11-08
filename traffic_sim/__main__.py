import argparse
import logging
import sys
from pathlib import Path

from . import config, i18n
from .i18n import tr
from .world import MapError, World


def resolve_map(value: str) -> Path:
    """Accept a file path or the name of a bundled map (e.g. 'small')."""
    path = Path(value)
    if path.exists():
        return path
    bundled = config.MAP_DIR / f"{path.stem}.txt"
    return bundled if bundled.exists() else path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    # read --lang first, so that the help texts and errors below are already in that language
    lang_parser = argparse.ArgumentParser(add_help=False)
    lang_parser.add_argument("--lang", choices=i18n.LANGUAGES, default=i18n.DEFAULT_LANGUAGE)
    i18n.set_language(lang_parser.parse_known_args(argv)[0].lang)

    bundled = ", ".join(sorted(p.stem for p in config.MAP_DIR.glob("*.txt")))
    parser = argparse.ArgumentParser(prog="traffic-sim", description=tr("cli_description"))
    parser.add_argument("--map", default=str(config.DEFAULT_MAP), help=tr("cli_map", maps=bundled))
    parser.add_argument("--cars", type=int, default=config.NORMAL_CARS, help=tr("cli_cars"))
    parser.add_argument("--right-cars", type=int, default=config.RIGHT_CARS, help=tr("cli_right_cars"))
    parser.add_argument("--seed", type=int, default=None, help=tr("cli_seed"))
    parser.add_argument("--lang", choices=i18n.LANGUAGES, default=i18n.DEFAULT_LANGUAGE, help=tr("cli_lang"))
    args = parser.parse_args(argv)
    if args.cars < 0 or args.right_cars < 0:
        parser.error(tr("negative_cars"))

    try:
        args.world = World.from_file(resolve_map(args.map))
    except MapError as error:
        parser.error(str(error))
    total, lanes = args.cars + args.right_cars, len(args.world.lane_tiles)
    if total > lanes:
        parser.error(tr("too_many_cars", total=total, lanes=lanes))
    return args


def set_windows_app_id() -> None:
    """Make Windows show our own icon in the taskbar instead of the Python one."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(config.APP_USER_MODEL_ID)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)
    set_windows_app_id()

    from PySide6.QtWidgets import QApplication

    from .app import MainWindow

    app = QApplication(sys.argv[:1])
    window = MainWindow(args.world, args.cars, args.right_cars, seed=args.seed)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
