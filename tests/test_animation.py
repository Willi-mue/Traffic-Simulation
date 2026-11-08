import math

import pytest

from traffic_sim import config
from traffic_sim.animation import CarAnimator, smooth_damp
from traffic_sim.traffic import Traffic
from traffic_sim.world import World

FRAME = 1 / 60


def test_smooth_damp_reaches_target_without_overshoot():
    value, velocity = 0.0, 0.0
    values = []
    for _ in range(120):
        value, velocity = smooth_damp(value, 1.0, velocity, smooth_time=0.1, dt=FRAME)
        values.append(value)
    assert all(v <= 1.0 for v in values)
    assert values == sorted(values)  # never goes back
    assert value == pytest.approx(1.0, abs=1e-3)


def test_smooth_damp_starts_and_stops_softly():
    value, velocity = 0.0, 0.0
    steps = []
    for _ in range(60):
        new, velocity = smooth_damp(value, 1.0, velocity, smooth_time=0.2, dt=FRAME)
        steps.append(new - value)
        value = new
    biggest = max(steps)
    assert steps[0] < biggest  # accelerates
    assert steps[-1] < biggest / 5  # slows down at the end


def make_traffic():
    world = World.from_file(config.MAP_DIR / "map1.txt")
    return Traffic(world, normal_cars=30, right_cars=20, seed=5)


def test_new_cars_appear_at_their_tile():
    traffic = make_traffic()
    poses = CarAnimator().update(traffic.cars, FRAME, smooth_time=0.08)
    for car in traffic.cars:
        assert (poses[car].x, poses[car].y) == (car.x + 0.5, car.y + 0.5)
        assert poses[car].angle == car.heading.angle


def test_drawn_cars_move_smoothly_and_follow_the_simulation():
    traffic = make_traffic()
    animator = CarAnimator()
    animator.update(traffic.cars, FRAME, 0.08)
    biggest_jump = 0.0
    for _ in range(300):  # 300 ticks of 100 ms, 6 frames each
        traffic.step()
        for _ in range(6):
            before = {car: (p.x, p.y) for car, p in animator.poses.items()}
            poses = animator.update(traffic.cars, FRAME, 0.08)
            for car, (bx, by) in before.items():
                biggest_jump = max(biggest_jump, math.hypot(poses[car].x - bx, poses[car].y - by))
    assert biggest_jump < 0.5  # never more than half a tile per frame
    for car in traffic.cars:  # drawn position stays close to the simulated one
        pose = animator.poses[car]
        assert math.hypot(pose.x - (car.x + 0.5), pose.y - (car.y + 0.5)) < 1.5


def test_restart_forgets_old_cars():
    animator = CarAnimator()
    old, new = make_traffic(), make_traffic()
    animator.update(old.cars, FRAME, 0.08)
    animator.update(new.cars, FRAME, 0.08)
    assert set(animator.poses) == set(new.cars)


def test_long_pause_does_not_teleport():
    traffic = make_traffic()
    animator = CarAnimator()
    animator.update(traffic.cars, FRAME, 0.08)
    for _ in range(3):
        traffic.step()
    car = next(c for c in traffic.cars if (c.x, c.y) != (c.prev_x, c.prev_y))
    before = (animator.poses[car].x, animator.poses[car].y)
    animator.update(traffic.cars, dt=5.0, smooth_time=0.08)  # e.g. window was dragged for 5 s
    after = (animator.poses[car].x, animator.poses[car].y)
    assert math.hypot(after[0] - before[0], after[1] - before[1]) < 3.1
