"""The simulation: map, traffic lights and all cars."""

import random
from collections import Counter

from . import config
from .car import Behavior, Car, StepResult
from .i18n import tr
from .traffic_light import TrafficLights
from .world import World


class Traffic:
    def __init__(
        self,
        world: World,
        normal_cars: int,
        right_cars: int,
        seed: int | None = None,
        move_probability: float = config.MOVE_PROBABILITY,
    ):
        self.world = world
        self.normal_cars = normal_cars
        self.right_cars = right_cars
        self.move_probability = move_probability
        self.rng = random.Random(seed)
        self.lights = TrafficLights(world.intersections)
        self.tick_count = 0
        self.cars = self._spawn_cars()

        self.last_results: Counter[StepResult] = Counter()
        # moving averages of the share of cars per result, for the overlay
        self.average_share: dict[StepResult, float] = dict.fromkeys(StepResult, 0.0)

    def _spawn_cars(self) -> list[Car]:
        total = self.normal_cars + self.right_cars
        free_tiles = self.world.lane_tiles
        if total > len(free_tiles):
            raise ValueError(tr("too_many_cars", total=total, lanes=len(free_tiles)))

        behaviors = [Behavior.NORMAL] * self.normal_cars + [Behavior.RIGHT] * self.right_cars
        positions = self.rng.sample(free_tiles, total)
        return [
            Car(car_id, behavior, x, y, self.world)
            for car_id, (behavior, (x, y)) in enumerate(zip(behaviors, positions, strict=True))
        ]

    def step(self) -> int:
        """Advance the simulation by one tick. Returns how many cars moved."""
        self.lights.tick()
        self.tick_count += 1
        occupied = {car.tile for car in self.cars}
        self.last_results = Counter(
            car.step(occupied, self.lights, self.rng, self.move_probability) for car in self.cars
        )
        self._update_statistics()
        return self.last_results[StepResult.MOVED]

    def _update_statistics(self) -> None:
        if not self.cars:
            return
        # the first tick fills the average directly, later ticks blend in
        weight = 1.0 if self.tick_count == 1 else config.STATS_SMOOTHING
        for result in StepResult:
            share = self.last_results[result] / len(self.cars)
            self.average_share[result] += weight * (share - self.average_share[result])
