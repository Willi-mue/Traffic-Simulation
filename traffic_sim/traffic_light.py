"""Traffic light phases.

Every intersection with a light has its own TrafficLight. A light gives green to one axis
(vertical or horizontal) at a time: green -> yellow -> the other axis gets green -> ...
"""

from enum import Enum

from . import config
from .direction import Direction
from .i18n import tr
from .world import Intersection


class Signal(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class TrafficLight:
    def __init__(
        self,
        switch_interval: int = config.LIGHT_SWITCH_INTERVAL,
        yellow_ticks: int = config.LIGHT_YELLOW_TICKS,
        offset: int = 0,
    ):
        if not 0 <= yellow_ticks < switch_interval:
            raise ValueError(tr("yellow_too_long"))
        self.switch_interval = switch_interval
        self.yellow_ticks = yellow_ticks
        self.tick_count = offset

    def tick(self) -> None:
        self.tick_count += 1

    @property
    def vertical_turn(self) -> bool:
        """True while the vertical axis has green or yellow."""
        return self.tick_count % (2 * self.switch_interval) < self.switch_interval

    def signal(self, direction: Direction) -> Signal:
        if direction.is_vertical != self.vertical_turn:
            return Signal.RED
        if self.tick_count % self.switch_interval >= self.switch_interval - self.yellow_ticks:
            return Signal.YELLOW
        return Signal.GREEN


class TrafficLights:
    """All traffic lights of a map, one per intersection that has a 'T'."""

    def __init__(
        self,
        intersections: list[Intersection],
        switch_interval: int = config.LIGHT_SWITCH_INTERVAL,
        yellow_ticks: int = config.LIGHT_YELLOW_TICKS,
        offset_step: int = config.LIGHT_OFFSET_STEP,
    ):
        lighted = [inter for inter in intersections if inter.has_light]
        self.by_intersection: dict[Intersection, TrafficLight] = {
            inter: TrafficLight(switch_interval, yellow_ticks, offset=i * offset_step)
            for i, inter in enumerate(lighted)
        }

    def tick(self) -> None:
        for light in self.by_intersection.values():
            light.tick()

    def signal(self, intersection: Intersection, direction: Direction) -> Signal | None:
        """Signal for a car entering the intersection in this direction; None without a light."""
        light = self.by_intersection.get(intersection)
        return None if light is None else light.signal(direction)
