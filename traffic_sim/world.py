"""Loading, validating and analysing the street map.

Coordinates are always (x, y): x = column, y = row.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .direction import LANE_CHARS, Direction
from .i18n import tr

log = logging.getLogger(__name__)

INTERSECTION = "."
TRAFFIC_LIGHT = "T"
SCENERY = set(" |-abcd")
ALLOWED_CHARS = set(LANE_CHARS) | {INTERSECTION, TRAFFIC_LIGHT} | SCENERY

Tile = tuple[int, int]

# Lines in the map ('-', '|', corners) run from the tile center to the middle of some tile edges.
LINE_SEGMENTS = {
    "-": {Direction.LEFT, Direction.RIGHT},
    "|": {Direction.UP, Direction.DOWN},
    "a": {Direction.RIGHT, Direction.DOWN},  # corner top left
    "b": {Direction.LEFT, Direction.DOWN},  # corner top right
    "c": {Direction.RIGHT, Direction.UP},  # corner bottom left
    "d": {Direction.LEFT, Direction.UP},  # corner bottom right
}

# Each tile is split into four quarters. A line segment separates the two quarters it runs between.
TL, TR, BL, BR = (0, 0), (1, 0), (0, 1), (1, 1)
_SEGMENT_WALL = {
    Direction.UP: (TL, TR),
    Direction.DOWN: (BL, BR),
    Direction.LEFT: (TL, BL),
    Direction.RIGHT: (TR, BR),
}


class MapError(ValueError):
    """The map file cannot be used."""


@dataclass
class StopPosition:
    """Where cars coming from one direction wait for the traffic light of an intersection."""

    intersection: "Intersection"
    direction: Direction
    tile: Tile  # cars wait on this tile
    line: tuple[tuple[float, float], tuple[float, float]]  # stop line, in tile coordinates
    light: tuple[float, float]  # position of the traffic light, in tile coordinates


@dataclass(eq=False)  # compared by identity, so it can be used as a dict key
class Intersection:
    tiles: set[Tile]
    has_light: bool = False
    # lane tiles directly in front of the intersection, with the direction that enters it
    entries: list[tuple[Tile, Direction]] = field(default_factory=list)
    stops: list[StopPosition] = field(default_factory=list)

    def __post_init__(self):
        xs = [x for x, _ in self.tiles]
        ys = [y for _, y in self.tiles]
        self.left, self.right = min(xs), max(xs)
        self.top, self.bottom = min(ys), max(ys)

    def contains(self, x: int, y: int, margin: int = 0) -> bool:
        return (
            self.left - margin <= x <= self.right + margin and self.top - margin <= y <= self.bottom + margin
        )


class World:
    def __init__(self, rows: list[str], name: str = "<map>"):
        self.name = name
        self.rows = self._validate(rows)
        self.height = len(self.rows)
        self.width = len(self.rows[0])

        self.lane_tiles: list[Tile] = [
            (x, y) for y, row in enumerate(self.rows) for x, char in enumerate(row) if char in LANE_CHARS
        ]
        self.lights: list[Tile] = [
            (x, y) for y, row in enumerate(self.rows) for x, char in enumerate(row) if char == TRAFFIC_LIGHT
        ]
        self.intersections = self._find_intersections()
        self.intersection_at: dict[Tile, Intersection] = {
            tile: inter for inter in self.intersections for tile in inter.tiles
        }
        self._assign_lights()
        self.line_segments = self._find_line_segments()
        self.road_quarters = self._find_road_quarters()
        self.stop_at: dict[tuple[Tile, Direction], StopPosition] = {}
        for inter in self.intersections:
            if inter.has_light:
                for tile, direction in inter.entries:
                    stop = self._stop_position(inter, tile, direction)
                    inter.stops.append(stop)
                    self.stop_at[(stop.tile, direction)] = stop

    @classmethod
    def from_file(cls, path: str | Path) -> "World":
        path = Path(path)
        try:
            with open(path, encoding="utf-8") as file:
                rows = file.read().splitlines()
        except OSError as error:
            raise MapError(tr("map_unreadable", path=path, reason=error.strerror)) from error
        return cls(rows, name=str(path))

    # ---- queries -------------------------------------------------------

    def char(self, x: int, y: int) -> str:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.rows[y][x]
        return " "

    def lane_direction(self, x: int, y: int) -> Direction | None:
        return LANE_CHARS.get(self.char(x, y))

    def is_intersection(self, x: int, y: int) -> bool:
        return self.char(x, y) == INTERSECTION

    def is_drivable(self, x: int, y: int) -> bool:
        return self.char(x, y) in LANE_CHARS or self.is_intersection(x, y)

    def is_road_quarter(self, x: int, y: int, quarter: tuple[int, int]) -> bool:
        return (2 * x + quarter[0], 2 * y + quarter[1]) in self.road_quarters

    def is_lane_separator(self, x: int, y: int) -> bool:
        """A '-' or '|' with road on both sides is a lane marking, otherwise it is a road edge."""
        char = self.char(x, y)
        if char == "-":
            return self.is_road_quarter(x, y, TL) and self.is_road_quarter(x, y, BL)
        if char == "|":
            return self.is_road_quarter(x, y, TL) and self.is_road_quarter(x, y, TR)
        return False

    # ---- loading -------------------------------------------------------

    def _validate(self, rows: list[str]) -> list[str]:
        while rows and not rows[-1].strip():
            rows = rows[:-1]
        if not rows:
            raise MapError(tr("map_empty", name=self.name))

        for y, row in enumerate(rows):
            for x, char in enumerate(row):
                if char not in ALLOWED_CHARS:
                    raise MapError(
                        tr("map_unknown_char", name=self.name, char=char, line=y + 1, column=x + 1)
                    )

        width = max(len(row) for row in rows)
        return [row.ljust(width) for row in rows]

    def _find_intersections(self) -> list[Intersection]:
        """Group '.' tiles that are connected by short lane pieces into intersections."""
        dots = [
            (x, y) for y, row in enumerate(self.rows) for x, char in enumerate(row) if char == INTERSECTION
        ]
        parent = {dot: dot for dot in dots}

        def find(tile: Tile) -> Tile:
            while parent[tile] != tile:
                parent[tile] = parent[parent[tile]]
                tile = parent[tile]
            return tile

        for x, y in dots:
            for dx, dy in ((1, 0), (0, 1)):
                for distance in range(1, config.MAX_INTERSECTION_SIZE + 1):
                    nx, ny = x + dx * distance, y + dy * distance
                    if self.is_intersection(nx, ny):
                        parent[find((nx, ny))] = find((x, y))
                        break
                    if self.char(nx, ny) not in LANE_CHARS:
                        break

        groups: dict[Tile, set[Tile]] = {}
        for dot in dots:
            groups.setdefault(find(dot), set()).add(dot)
        return [Intersection(tiles) for tiles in groups.values()]

    def _nearest_corner(self, entry: Tile, side: Direction, back: Direction) -> Tile | None:
        """Nearest curb corner ('a'-'d') to the given side of the lane, at or before the entry."""
        for distance in range(1, 10):
            for k in range(1, distance + 1):
                j = distance - k
                x, y = entry[0] + side.dx * k + back.dx * j, entry[1] + side.dy * k + back.dy * j
                if self.char(x, y) in "abcd":
                    return x, y
        return None

    def _behind_road_edge(self, point: tuple[float, float], side: Direction) -> tuple[float, float]:
        """First spot next to the road, going from point (a lane center) towards side."""
        x, y = point
        for step in range(1, 20):
            px, py = x + side.dx * 0.25 * step, y + side.dy * 0.25 * step
            if (int(px * 2), int(py * 2)) not in self.road_quarters:
                return px + side.dx * 0.1, py + side.dy * 0.1
        return x + side.dx * 0.7, y + side.dy * 0.7

    def _stop_position(self, inter: Intersection, entry: Tile, direction: Direction) -> StopPosition:
        """Stop line where the cross street begins (at the curb corner), traffic light on the right
        corner (or right behind the right road edge), and the last lane tile completely before the line."""
        side = direction.turn_right()
        back = direction.turn_right().turn_right()
        right_corner = self._nearest_corner(entry, side, back)
        corner = right_corner or self._nearest_corner(entry, side.turn_right().turn_right(), back)

        lane_center = (entry[0] + 0.5, entry[1] + 0.5)
        if corner is None:
            # no curb nearby: stop line right in front of the intersection
            line_at = (lane_center[0] + direction.dx * 0.5, lane_center[1] + direction.dy * 0.5)
        elif direction.is_vertical:  # stop line at the height of the corner, slightly before it
            line_at = (lane_center[0], corner[1] + 0.5 - direction.dy * 0.15)
        else:
            line_at = (corner[0] + 0.5 - direction.dx * 0.15, lane_center[1])

        if right_corner is not None:  # on the grass behind the corner
            light = (
                right_corner[0] + 0.5 + (side.dx + back.dx) * 0.3,
                right_corner[1] + 0.5 + (side.dy + back.dy) * 0.3,
            )
        else:
            light = self._behind_road_edge(line_at, side)

        stop_tile = entry
        if corner is not None:
            # walk back until the whole tile lies before the stop line
            stop_tile = entry
            for _ in range(4):
                center = (stop_tile[0] + 0.5, stop_tile[1] + 0.5)
                ahead = (line_at[0] - center[0]) * direction.dx + (line_at[1] - center[1]) * direction.dy
                previous = back.step(*stop_tile)
                if ahead >= 0.5 or self.lane_direction(*previous) != direction:
                    break
                stop_tile = previous

        # stop line across the whole half of the road: from the center line to the right road edge
        edge = self._behind_road_edge(line_at, side)
        to_edge = abs((edge[0] - line_at[0]) * side.dx + (edge[1] - line_at[1]) * side.dy) - 0.2
        to_center = 0.42
        opposite = back
        for k in range(1, 9):
            left = (entry[0] - side.dx * k, entry[1] - side.dy * k)
            if self.lane_direction(*left) == opposite:
                to_center = k / 2 - 0.1
                break
        line = (
            (line_at[0] - side.dx * to_center, line_at[1] - side.dy * to_center),
            (line_at[0] + side.dx * to_edge, line_at[1] + side.dy * to_edge),
        )
        return StopPosition(inter, direction, stop_tile, line, light)

    def _find_line_segments(self) -> dict[Tile, set[Direction]]:
        """Line segments per tile. Where a line ends right next to another line (e.g. '|---'),
        the two are joined like a T, so there is no gap between them."""
        segments = {
            (x, y): set(LINE_SEGMENTS[char])
            for y, row in enumerate(self.rows)
            for x, char in enumerate(row)
            if char in LINE_SEGMENTS
        }
        for (x, y), own in segments.items():
            for direction in Direction:
                neighbor = segments.get(direction.step(x, y))
                opposite = direction.turn_right().turn_right()
                if neighbor is not None and opposite in LINE_SEGMENTS[self.char(*direction.step(x, y))]:
                    own.add(direction)
        return segments

    def _find_road_quarters(self) -> set[Tile]:
        """Road surface: all tile quarters reachable from lanes without crossing a line.

        Works on a grid with twice the resolution of the map, cell (2x + qx, 2y + qy) is quarter
        (qx, qy) of tile (x, y).
        """
        seeds = [
            (2 * x + qx, 2 * y + qy)
            for y, row in enumerate(self.rows)
            for x, char in enumerate(row)
            if char in LANE_CHARS or char in (INTERSECTION, TRAFFIC_LIGHT)
            for qx, qy in (TL, TR, BL, BR)
        ]
        road = set(seeds)
        stack = list(seeds)
        while stack:
            cx, cy = stack.pop()
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if not (0 <= nx < 2 * self.width and 0 <= ny < 2 * self.height) or (nx, ny) in road:
                    continue
                if (cx // 2, cy // 2) == (nx // 2, ny // 2):  # same tile: a line may be in between
                    segments = self.line_segments.get((cx // 2, cy // 2), ())
                    pair = {(cx % 2, cy % 2), (nx % 2, ny % 2)}
                    if any(set(_SEGMENT_WALL[s]) == pair for s in segments):
                        continue
                road.add((nx, ny))
                stack.append((nx, ny))
        return road

    def _assign_lights(self) -> None:
        for x, y in self.lights:
            matches = [inter for inter in self.intersections if inter.contains(x, y, margin=1)]
            if not matches:
                log.warning(tr("light_without_intersection", name=self.name, line=y + 1, column=x + 1))
            for inter in matches:
                inter.has_light = True

        for inter in self.intersections:
            for tx, ty in inter.tiles:
                for direction in Direction:
                    before = (tx - direction.dx, ty - direction.dy)
                    if not inter.contains(*before) and self.lane_direction(*before) == direction:
                        inter.entries.append((before, direction))
