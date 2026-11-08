import pytest

from traffic_sim import config
from traffic_sim.direction import Direction
from traffic_sim.traffic_light import Signal, TrafficLight, TrafficLights
from traffic_sim.world import World


def signals_over_time(light: TrafficLight, direction: Direction, ticks: int) -> list[Signal]:
    result = []
    for _ in range(ticks):
        result.append(light.signal(direction))
        light.tick()
    return result


def test_phase_sequence_with_yellow():
    g, y, r = Signal.GREEN, Signal.YELLOW, Signal.RED
    vertical = signals_over_time(TrafficLight(switch_interval=4, yellow_ticks=1), Direction.UP, 8)
    horizontal = signals_over_time(TrafficLight(switch_interval=4, yellow_ticks=1), Direction.LEFT, 8)
    assert vertical == [g, g, g, y, r, r, r, r]
    assert horizontal == [r, r, r, r, g, g, g, y]


def test_never_both_axes_green():
    light = TrafficLight(switch_interval=7, yellow_ticks=2)
    for _ in range(50):
        moving = [d for d in Direction if light.signal(d) is not Signal.RED]
        assert all(d.is_vertical for d in moving) or not any(d.is_vertical for d in moving)
        light.tick()


def test_invalid_yellow_raises():
    with pytest.raises(ValueError):
        TrafficLight(switch_interval=4, yellow_ticks=4)


def test_each_intersection_has_own_phase():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    lights = TrafficLights(world.intersections, switch_interval=32, yellow_ticks=4, offset_step=16)
    first, second = lights.by_intersection.values()
    assert first.tick_count != second.tick_count

    differing = 0
    for _ in range(64):
        if first.signal(Direction.UP) != second.signal(Direction.UP):
            differing += 1
        lights.tick()
    assert differing > 0


def test_no_signal_without_light():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    lights = TrafficLights(world.intersections)
    unlit = next(inter for inter in world.intersections if not inter.has_light)
    assert lights.signal(unlit, Direction.UP) is None
