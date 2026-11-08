"""User-facing texts in German (default) and English."""

DEFAULT_LANGUAGE = "de"
LANGUAGES = ("de", "en")

TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "window_title": "Verkehrssimulation",
        "state_running": "läuft",
        "state_paused": "pausiert",
        "hud_tick": "Tick: {ms} ms  ·  {state}",
        "hud_cars": "Autos: {normal} zufällig, {right} rechts",
        "hud_stats": "Fahrend: {moving:4.0%}  ·  wartend: {waiting:4.0%} (Ampel {light:.0%})",
        "hud_hint": "H: Hilfe  ·  L: English",
        "help": (
            "E           Pause / weiter\n"
            "W / S       schneller / langsamer\n"
            "Q           Fahrtrichtungen an/aus\n"
            "Pfeiltasten Karte verschieben\n"
            "Maus ziehen Karte verschieben\n"
            "Mausrad     Zoom\n"
            "R           Neustart\n"
            "H           Hilfe an/aus\n"
            "L           Sprache wechseln\n"
            "Esc         Beenden"
        ),
        "map_unreadable": "Karte kann nicht gelesen werden: {path} ({reason})",
        "map_empty": "{name}: Karte ist leer",
        "map_unknown_char": "{name}: unbekanntes Zeichen {char!r} in Zeile {line}, Spalte {column}",
        "light_without_intersection": "{name}: Ampel bei Zeile {line}, Spalte {column} "
        "gehört zu keiner Kreuzung",
        "car_off_road": "Auto {car} steht neben der Straße bei {tile}",
        "car_no_exit": "Auto {car} findet an der Kreuzung {tile} keine Ausfahrt",
        "too_many_cars": "{total} Autos passen nicht auf {lanes} Straßenfelder",
        "negative_cars": "Anzahl der Autos darf nicht negativ sein",
        "yellow_too_long": "Die Gelbphase muss kürzer als die Ampelphase sein",
        "cli_description": "Verkehrssimulation",
        "cli_map": "Kartendatei oder Name einer mitgelieferten Karte ({maps})",
        "cli_cars": "Autos, die an Kreuzungen zufällig abbiegen",
        "cli_right_cars": "Autos, die immer rechts abbiegen",
        "cli_seed": "Zufallsstartwert für reproduzierbare Läufe",
        "cli_lang": "Sprache der Oberfläche (de oder en)",
    },
    "en": {
        "window_title": "Traffic Simulation",
        "state_running": "running",
        "state_paused": "paused",
        "hud_tick": "Tick: {ms} ms  ·  {state}",
        "hud_cars": "Cars: {normal} random, {right} turn right",
        "hud_stats": "Driving: {moving:4.0%}  ·  waiting: {waiting:4.0%} (lights {light:.0%})",
        "hud_hint": "H: help  ·  L: Deutsch",
        "help": (
            "E           pause / resume\n"
            "W / S       faster / slower\n"
            "Q           driving directions on/off\n"
            "Arrow keys  move map\n"
            "Mouse drag  move map\n"
            "Mouse wheel zoom\n"
            "R           restart\n"
            "H           help on/off\n"
            "L           switch language\n"
            "Esc         exit"
        ),
        "map_unreadable": "Cannot read map: {path} ({reason})",
        "map_empty": "{name}: map is empty",
        "map_unknown_char": "{name}: unknown character {char!r} in line {line}, column {column}",
        "light_without_intersection": "{name}: traffic light at line {line}, column {column} "
        "does not belong to an intersection",
        "car_off_road": "Car {car} is off the road at {tile}",
        "car_no_exit": "Car {car} finds no exit at intersection {tile}",
        "too_many_cars": "{total} cars do not fit on {lanes} road tiles",
        "negative_cars": "number of cars must not be negative",
        "yellow_too_long": "The yellow phase must be shorter than the light phase",
        "cli_description": "Traffic simulation",
        "cli_map": "map file or name of a bundled map ({maps})",
        "cli_cars": "cars that turn randomly at intersections",
        "cli_right_cars": "cars that always turn right",
        "cli_seed": "random seed for reproducible runs",
        "cli_lang": "user interface language (de or en)",
    },
}

_current = DEFAULT_LANGUAGE


def set_language(language: str) -> None:
    global _current
    if language not in TEXTS:
        raise ValueError(f"unknown language: {language}")
    _current = language


def get_language() -> str:
    return _current


def next_language() -> str:
    """The language after the current one, for toggling."""
    return LANGUAGES[(LANGUAGES.index(_current) + 1) % len(LANGUAGES)]


def tr(key: str, **values) -> str:
    """Text for key in the current language, with {placeholders} filled in."""
    return TEXTS[_current][key].format(**values)
