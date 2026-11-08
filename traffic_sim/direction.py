"""Driving directions on the grid."""

from enum import Enum


class Direction(Enum):
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @property
    def is_vertical(self) -> bool:
        return self in (Direction.UP, Direction.DOWN)

    @property
    def angle(self) -> float:
        """Rotation in degrees for drawing (0 = pointing right, clockwise)."""
        return _ANGLES[self]

    def turn_right(self) -> "Direction":
        return _CLOCKWISE[(_CLOCKWISE.index(self) + 1) % 4]

    def turn_left(self) -> "Direction":
        return _CLOCKWISE[(_CLOCKWISE.index(self) - 1) % 4]

    def step(self, x: int, y: int) -> tuple[int, int]:
        """The tile one step ahead in this direction."""
        return x + self.dx, y + self.dy


_CLOCKWISE = [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
_ANGLES = {Direction.RIGHT: 0.0, Direction.DOWN: 90.0, Direction.LEFT: 180.0, Direction.UP: 270.0}

LANE_CHARS = {
    ">": Direction.RIGHT,
    "<": Direction.LEFT,
    "^": Direction.UP,
    "v": Direction.DOWN,
}
