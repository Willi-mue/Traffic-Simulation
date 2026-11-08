"""Smooth car movement for drawing, independent of the simulation ticks.

The simulation moves cars tile by tile. For drawing, every car has its own position that follows
the simulated position like a critically damped spring: it speeds up and slows down smoothly,
cuts corners in a curve and turns in the direction it actually moves.
"""

import math
from dataclasses import dataclass

from .car import Car

MIN_TURN_SPEED = 0.05  # tiles per second; slower cars keep their angle


def interpolate_angle(start: float, end: float, progress: float) -> float:
    """Angle between start and end (degrees), taking the shorter way around."""
    diff = math.remainder(end - start, 360.0)
    return start + diff * progress


@dataclass
class CarPose:
    x: float  # tile coordinates of the car center
    y: float
    angle: float  # degrees, 0 = pointing right
    vx: float = 0.0  # tiles per second
    vy: float = 0.0


def smooth_damp(current: float, target: float, velocity: float, smooth_time: float, dt: float):
    """Move current towards target without overshooting (critically damped spring).

    Returns the new value and the new velocity. smooth_time is roughly the time to reach the target.
    """
    smooth_time = max(1e-4, smooth_time)
    omega = 2.0 / smooth_time
    x = omega * dt
    decay = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    change = current - target
    temp = (velocity + omega * change) * dt
    new_velocity = (velocity - omega * temp) * decay
    new_value = target + (change + temp) * decay
    if (target - current > 0) == (new_value > target):  # would overshoot: stop exactly at the target
        return target, 0.0
    return new_value, new_velocity


class CarAnimator:
    def __init__(self):
        self.poses: dict[Car, CarPose] = {}

    def update(self, cars: list[Car], dt: float, smooth_time: float) -> dict[Car, CarPose]:
        dt = min(max(dt, 0.0), 0.1)  # a long pause (e.g. window dragged) must not make cars jump
        poses = {}
        for car in cars:
            target_x, target_y = car.x + 0.5, car.y + 0.5
            pose = self.poses.get(car)
            if pose is None:
                pose = CarPose(target_x, target_y, car.heading.angle)
            elif dt > 0:
                pose.x, pose.vx = smooth_damp(pose.x, target_x, pose.vx, smooth_time, dt)
                pose.y, pose.vy = smooth_damp(pose.y, target_y, pose.vy, smooth_time, dt)
                if math.hypot(pose.vx, pose.vy) > MIN_TURN_SPEED:
                    moving_angle = math.degrees(math.atan2(pose.vy, pose.vx))
                    pose.angle = interpolate_angle(pose.angle, moving_angle, min(1.0, dt / (smooth_time / 2)))
            poses[car] = pose
        self.poses = poses  # forget cars that no longer exist
        return poses
