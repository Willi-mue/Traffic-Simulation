"""A single car and its driving rules."""

import logging
import random
from enum import Enum

from .direction import Direction
from .i18n import tr
from .traffic_light import Signal, TrafficLights
from .world import Tile, World

log = logging.getLogger(__name__)


class Behavior(Enum):
    NORMAL = "normal"  # picks a random way at intersections
    RIGHT = "right"  # turns right whenever possible


class StepResult(Enum):
    MOVED = "moved"
    BLOCKED = "blocked"  # another car is in the way
    LIGHT = "light"  # waiting at a red or yellow light
    IDLE = "idle"  # could have moved but randomly did not (move_probability)
    STUCK = "stuck"  # has no direction, e.g. dead end in the map


class Car:
    def __init__(self, car_id: int, behavior: Behavior, x: int, y: int, world: World):
        self.car_id = car_id
        self.behavior = behavior
        self.world = world
        self.x, self.y = x, y
        # position before the last tick, used to animate the movement
        self.prev_x, self.prev_y = x, y

        self.direction: Direction | None = world.lane_direction(x, y)
        # direction of the last movement and the one before, used to rotate the car smoothly when drawing
        self.heading: Direction = self.direction or Direction.RIGHT
        self.prev_heading: Direction = self.heading

    @property
    def tile(self) -> Tile:
        return self.x, self.y

    def next_tile(self) -> Tile | None:
        if self.direction is None:
            return None
        return self.direction.step(self.x, self.y)

    def step(
        self, occupied: set[Tile], lights: TrafficLights, rng: random.Random, move_probability: float
    ) -> StepResult:
        """Try to move one tile ahead."""
        self.prev_x, self.prev_y = self.x, self.y
        self.prev_heading = self.heading

        target = self.next_tile()
        if target is None:
            return StepResult.STUCK
        if target in occupied:
            return StepResult.BLOCKED
        if self.must_stop_at_light(lights):
            return StepResult.LIGHT
        if rng.random() >= move_probability:
            return StepResult.IDLE

        occupied.discard(self.tile)
        occupied.add(target)
        self.x, self.y = target
        self.heading = self.direction
        self.direction = self.pick_direction(rng)
        return StepResult.MOVED

    def must_stop_at_light(self, lights: TrafficLights) -> bool:
        """True when the car waits at a stop line and the light is not green for it.

        Cars already past the stop line keep going, so they clear the intersection.
        """
        stop = self.world.stop_at.get((self.tile, self.direction))
        if stop is None:
            return False
        signal = lights.signal(stop.intersection, self.direction)
        return signal is not None and signal is not Signal.GREEN

    def pick_direction(self, rng: random.Random) -> Direction | None:
        """Direction to take from the current tile."""
        lane = self.world.lane_direction(self.x, self.y)
        if lane is not None:
            return lane
        if not self.world.is_intersection(self.x, self.y):
            log.warning(tr("car_off_road", car=self.car_id, tile=self.tile))
            return None

        options = self.exit_options()
        if not options:
            log.warning(tr("car_no_exit", car=self.car_id, tile=self.tile))
            return None
        if self.behavior is Behavior.RIGHT:
            return options[0]
        return rng.choice(options)

    def exit_options(self) -> list[Direction]:
        """Possible ways out of an intersection tile, preferring right, then straight, then left."""
        current = self.direction or self.heading
        options = []
        for direction in (current.turn_right(), current, current.turn_left()):
            nx, ny = direction.step(self.x, self.y)
            fits_lane = self.world.lane_direction(nx, ny) == direction
            straight_into_intersection = direction == current and self.world.is_intersection(nx, ny)
            if fits_lane or straight_into_intersection:
                options.append(direction)
        return options
