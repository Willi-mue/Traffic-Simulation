import random

import pytest

from traffic_sim import config
from traffic_sim.car import Behavior, Car, StepResult
from traffic_sim.direction import Direction
from traffic_sim.traffic import Traffic
from traffic_sim.traffic_light import TrafficLights
from traffic_sim.world import MapError, World

# One four-way intersection with a traffic light, same layout as in map1.
CROSSING = [
    "    v   ^    ",
    "<<<<.<<<.<<<<",
    "    v T ^    ",
    ">>>>.>>>.>>>>",
    "    v   ^    ",
]


def make_world(rows=CROSSING) -> World:
    return World(list(rows))


# ---- world -----------------------------------------------------------------


def test_bundled_maps_load():
    for path in config.MAP_DIR.glob("*.txt"):
        world = World.from_file(path)
        assert world.lane_tiles
        assert any(i.has_light for i in world.intersections)


def test_unknown_char_reports_position():
    with pytest.raises(MapError, match="Zeile 2, Spalte 3"):
        World(["<<<", "<<+"])


def test_rows_are_padded_to_same_width():
    world = World([">>>>", ">>"])
    assert world.width == 4
    assert world.char(3, 1) == " "


def test_intersection_detection_and_light():
    world = make_world()
    assert len(world.intersections) == 1
    crossing = world.intersections[0]
    assert crossing.has_light
    assert crossing.tiles == {(4, 1), (8, 1), (4, 3), (8, 3)}
    entries = {direction for _, direction in crossing.entries}
    assert entries == set(Direction)


# ---- cars ------------------------------------------------------------------


def car_at(world, x, y, behavior=Behavior.NORMAL, car_id=0):
    return Car(car_id, behavior, x, y, world)


def lights_green_for(world, direction):
    """Traffic lights of the world, with green for the axis of the given direction."""
    lights = TrafficLights(world.intersections, switch_interval=10, yellow_ticks=2, offset_step=0)
    for light in lights.by_intersection.values():
        light.tick_count = 0 if direction.is_vertical else 10
    return lights


def test_car_moves_forward():
    world = make_world()
    car = car_at(world, 1, 3)  # on '>' lane
    result = car.step(
        {car.tile}, lights_green_for(world, Direction.RIGHT), random.Random(0), move_probability=1
    )
    assert result is StepResult.MOVED and car.tile == (2, 3)


def test_car_waits_for_car_in_front():
    world = make_world()
    car = car_at(world, 1, 3)
    occupied = {car.tile, (2, 3)}
    result = car.step(
        occupied, lights_green_for(world, Direction.RIGHT), random.Random(0), move_probability=1
    )
    assert result is StepResult.BLOCKED


def test_car_stops_at_red_light_and_goes_at_green():
    world = make_world()
    car = car_at(world, 3, 3)  # directly in front of the intersection, heading right
    red = lights_green_for(world, Direction.UP)
    assert car.must_stop_at_light(red)
    assert not car.must_stop_at_light(lights_green_for(world, Direction.RIGHT))


def test_car_inside_intersection_ignores_light():
    world = make_world()
    car = car_at(world, 4, 0)  # heading down, right above the intersection
    car.step({car.tile}, lights_green_for(world, Direction.DOWN), random.Random(0), move_probability=1)
    assert car.tile == (4, 1)
    # inside now: a red light must not stop it in the middle of the crossing
    assert not car.must_stop_at_light(lights_green_for(world, Direction.LEFT))


def test_right_car_turns_right():
    world = make_world()
    car = car_at(world, 3, 3, Behavior.RIGHT)  # heading right into (4, 3)
    car.step({car.tile}, lights_green_for(world, Direction.RIGHT), random.Random(0), move_probability=1)
    assert car.direction is Direction.DOWN


def test_no_exit_does_not_crash():
    world = World([">.", "  "])
    car = car_at(world, 0, 0)
    lights = TrafficLights(world.intersections)
    car.step({car.tile}, lights, random.Random(0), move_probability=1)
    assert car.tile == (1, 0)
    assert car.direction is None
    assert car.step({car.tile}, lights, random.Random(0), move_probability=1) is StepResult.STUCK


# ---- traffic ---------------------------------------------------------------


def test_spawn_positions_are_unique():
    world = make_world()
    total = len(world.lane_tiles)  # fill every single lane tile
    traffic = Traffic(world, normal_cars=total - 5, right_cars=5, seed=1)
    assert len({car.tile for car in traffic.cars}) == total


def test_too_many_cars_raises():
    world = make_world()
    with pytest.raises(ValueError):
        Traffic(world, normal_cars=len(world.lane_tiles) + 1, right_cars=0)


@pytest.mark.parametrize("map_name", ["map1", "small"])
def test_no_collisions_and_no_gridlock(map_name):
    world = World.from_file(config.MAP_DIR / f"{map_name}.txt")
    traffic = Traffic(world, normal_cars=25, right_cars=15, seed=42)
    moves = []
    for _ in range(2000):
        moves.append(traffic.step())
        assert len({car.tile for car in traffic.cars}) == len(traffic.cars)
    assert sum(moves[-200:]) / 200 > 10


def test_statistics_add_up_to_one():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    traffic = Traffic(world, normal_cars=30, right_cars=20, seed=3)
    for _ in range(300):
        traffic.step()
    assert sum(traffic.last_results.values()) == 50
    assert sum(traffic.average_share.values()) == pytest.approx(1.0)
    assert traffic.average_share[StepResult.MOVED] > 0.3


# ---- road surface ------------------------------------------------------------


def test_road_surface_stays_inside_curbs():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    assert all(world.is_road_quarter(x, y, q) for x, y in world.lane_tiles for q in ((0, 0), (1, 1)))
    # inside a block and in the closed lot at the bottom left there is no road
    assert not world.is_road_quarter(30, 7, (0, 0))
    assert not world.is_road_quarter(10, 37, (0, 0))


def test_lane_separator_vs_road_edge():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    assert world.char(5, 30) == "-" and world.is_lane_separator(5, 30)  # between two lanes
    assert world.char(10, 0) == "-" and not world.is_lane_separator(10, 0)  # outer frame


def test_line_ending_next_to_line_is_joined():
    world = World(["|--", "|  "])
    assert Direction.RIGHT in world.line_segments[(0, 0)]


# ---- stop lines and traffic light positions -----------------------------------


@pytest.mark.parametrize("map_name", ["map1", "small"])
def test_traffic_lights_stand_next_to_the_road(map_name):
    world = World.from_file(config.MAP_DIR / f"{map_name}.txt")
    stops = [stop for inter in world.intersections for stop in inter.stops]
    assert stops
    for stop in stops:
        lx, ly = stop.light
        assert (int(lx * 2), int(ly * 2)) not in world.road_quarters, stop


def test_cars_wait_before_the_cross_street():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    # southbound lane at x=25: the cross street's curb is at y=28.5, so cars wait on y=27, not y=28
    stop = world.stop_at[((25, 27), Direction.DOWN)]
    (_, y1), (_, y2) = stop.line
    assert y1 == y2 and 28 < y1 < 28.5
    assert ((25, 28), Direction.DOWN) not in world.stop_at


def test_car_waits_at_stop_line_on_red():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    car = car_at(world, 25, 27)
    red = lights_green_for(world, Direction.LEFT)
    assert car.step({car.tile}, red, random.Random(0), move_probability=1) is StepResult.LIGHT
    green = lights_green_for(world, Direction.DOWN)
    assert car.step({car.tile}, green, random.Random(0), move_probability=1) is StepResult.MOVED
    # past the stop line: keeps going even when red
    assert car.step({car.tile}, red, random.Random(0), move_probability=1) is StepResult.MOVED
