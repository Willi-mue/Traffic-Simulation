"""Drawing the map, traffic lights, cars and the info overlay.

Everything is drawn as vector shapes, so it stays sharp at every zoom level.
Positions inside a tile are given in tile units: (0, 0) is the top left corner, (0.5, 0.5) the center.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFontDatabase, QFontMetrics, QPainter, QPainterPath, QPen, QPixmap

from . import config
from .animation import CarPose
from .car import Car
from .direction import LANE_CHARS, Direction
from .traffic_light import Signal, TrafficLights
from .world import BL, BR, INTERSECTION, LINE_SEGMENTS, TL, TR, World

SIGNAL_COLORS = {
    Signal.GREEN: config.LIGHT_GREEN,
    Signal.YELLOW: config.LIGHT_YELLOW,
    Signal.RED: config.LIGHT_RED,
}

LIGHT_LENGTH = 0.8  # traffic light housing, along the driving direction (tile units)
LIGHT_WIDTH = 0.34
LAMP_ORDER = (Signal.GREEN, Signal.YELLOW, Signal.RED)  # from upstream to downstream


def _qcolor(rgb, alpha: int | None = None) -> QColor:
    color = QColor(*rgb)
    if alpha is not None:
        color.setAlpha(alpha)
    return color


class Renderer:
    def __init__(self):
        self.hud_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.hud_font.setPointSize(10)

    # ---- static map ------------------------------------------------------

    def render_map(
        self,
        world: World,
        tile: int,
        show_lines: bool,
        ox: int,
        oy: int,
        width: int,
        height: int,
        pixel_ratio: float = 1.0,
    ) -> QPixmap:
        """Draw the visible part of the map into a window-sized pixmap (cached by the window).

        pixel_ratio is the screen scaling (e.g. 1.25 at 125 %), so the map stays sharp.
        """
        pixmap = QPixmap(max(1, round(width * pixel_ratio)), max(1, round(height * pixel_ratio)))
        pixmap.setDevicePixelRatio(pixel_ratio)
        pixmap.fill(_qcolor(config.BACKGROUND_COLOR))
        painter = QPainter(pixmap)

        x0, x1 = max(0, -ox // tile), min(world.width, (width - ox) // tile + 1)
        y0, y1 = max(0, -oy // tile), min(world.height, (height - oy) // tile + 1)
        visible = [(x, y) for y in range(y0, y1) for x in range(x0, x1)]

        self._draw_road_surface(painter, world, visible, tile, ox, oy)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_lines(painter, world, visible, tile, ox, oy)
        self._draw_stop_lines(painter, world, tile, ox, oy)
        if show_lines:
            self._draw_guides(painter, world, visible, tile, ox, oy)

        painter.end()
        return pixmap

    @staticmethod
    def _draw_road_surface(painter, world: World, visible, tile: int, ox: int, oy: int) -> None:
        """Asphalt on every road quarter. Integer rectangles, so there are no seams between tiles."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_qcolor(config.ROAD_COLOR))
        left, right = tile // 2, tile - tile // 2
        for x, y in visible:
            px, py = ox + x * tile, oy + y * tile
            quarters = [q for q in (TL, TR, BL, BR) if world.is_road_quarter(x, y, q)]
            if len(quarters) == 4:
                painter.drawRect(px, py, tile, tile)
                continue
            for qx, qy in quarters:
                painter.drawRect(px + qx * left, py + qy * left, right if qx else left, right if qy else left)

    @staticmethod
    def _draw_lines(painter, world: World, visible, tile: int, ox: int, oy: int) -> None:
        """Road edges as solid curbs, lines between lanes as white markings."""
        curb = QPen(_qcolor(config.CURB_COLOR), max(1.0, tile * 0.14))
        curb.setCapStyle(Qt.PenCapStyle.SquareCap)
        marking = QPen(_qcolor(config.MARKING_COLOR), max(1.0, tile * 0.08))
        marking.setCapStyle(Qt.PenCapStyle.FlatCap)

        for x, y in visible:
            segments = world.line_segments.get((x, y))
            if not segments:
                continue
            if world.is_lane_separator(x, y):
                painter.setPen(marking)
                segments = LINE_SEGMENTS[world.char(x, y)]
            else:
                painter.setPen(curb)
            cx, cy = ox + (x + 0.5) * tile, oy + (y + 0.5) * tile
            for direction in segments:
                end = QPointF(cx + direction.dx * tile / 2, cy + direction.dy * tile / 2)
                painter.drawLine(QPointF(cx, cy), end)

    @staticmethod
    def _draw_stop_lines(painter, world: World, tile: int, ox: int, oy: int) -> None:
        pen = QPen(_qcolor(config.MARKING_COLOR), max(1.0, tile * 0.1))
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        for intersection in world.intersections:
            for stop in intersection.stops:
                (ax, ay), (bx, by) = stop.line
                painter.drawLine(
                    QPointF(ox + ax * tile, oy + ay * tile), QPointF(ox + bx * tile, oy + by * tile)
                )

    def _draw_guides(self, painter, world: World, visible, tile: int, ox: int, oy: int) -> None:
        """Direction arrows on lanes and dots on intersection tiles (toggled with Q)."""
        pen = QPen(_qcolor(config.GUIDE_COLOR), max(1.0, tile * 0.07))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        for x, y in visible:
            char = world.char(x, y)
            cx, cy = ox + (x + 0.5) * tile, oy + (y + 0.5) * tile
            if char in LANE_CHARS:
                painter.setPen(pen)
                self._draw_arrow(painter, cx, cy, tile, LANE_CHARS[char])
            elif char == INTERSECTION:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(_qcolor(config.GUIDE_COLOR))
                painter.drawEllipse(QPointF(cx, cy), tile * 0.08, tile * 0.08)

    @staticmethod
    def _draw_arrow(painter: QPainter, cx: float, cy: float, tile: float, direction: Direction) -> None:
        dx, dy = direction.dx, direction.dy
        px, py = -dy, dx  # perpendicular
        tip = QPointF(cx + dx * tile * 0.15, cy + dy * tile * 0.15)
        back = (cx - dx * tile * 0.1, cy - dy * tile * 0.1)
        path = QPainterPath(QPointF(back[0] + px * tile * 0.16, back[1] + py * tile * 0.16))
        path.lineTo(tip)
        path.lineTo(back[0] - px * tile * 0.16, back[1] - py * tile * 0.16)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    # ---- dynamic parts ---------------------------------------------------

    def draw_lights(
        self, painter: QPainter, world: World, lights: TrafficLights, tile: float, ox: float, oy: float
    ) -> None:
        """A traffic light with three lamps on the curb corner next to every stop line."""
        length, width = tile * LIGHT_LENGTH, tile * LIGHT_WIDTH
        lamp = width * 0.32
        housing = QRectF(-length / 2, -width / 2, length, width)
        painter.setPen(Qt.PenStyle.NoPen)
        for intersection in world.intersections:
            for stop in intersection.stops:
                signal = lights.signal(intersection, stop.direction)
                if signal is None:
                    continue
                painter.save()
                painter.translate(ox + stop.light[0] * tile, oy + stop.light[1] * tile)
                painter.rotate(stop.direction.angle)
                painter.setBrush(QColor(0, 0, 0, 90))  # shadow
                painter.drawRoundedRect(housing.translated(tile * 0.03, tile * 0.04), width / 3, width / 3)
                painter.setBrush(_qcolor(config.LIGHT_HOUSING))
                painter.drawRoundedRect(housing, width / 3, width / 3)
                for i, lamp_signal in enumerate(LAMP_ORDER):
                    center = QPointF((i - 1) * length / 3, 0)
                    color = SIGNAL_COLORS[lamp_signal]
                    if lamp_signal is signal:
                        painter.setBrush(_qcolor(color, 80))  # glow
                        painter.drawEllipse(center, lamp * 2.2, lamp * 2.2)
                        painter.setBrush(_qcolor(color))
                    else:
                        painter.setBrush(_qcolor(color, 45))
                    painter.drawEllipse(center, lamp, lamp)
                painter.restore()

    def draw_cars(
        self,
        painter: QPainter,
        cars: list[Car],
        poses: dict[Car, CarPose],
        tile: float,
        ox: float,
        oy: float,
    ) -> None:
        """Cars with shadow, windshield and headlights at their smoothly animated position."""
        painter.setPen(Qt.PenStyle.NoPen)
        length, width = tile * 0.78, tile * 0.46
        body = QRectF(-length / 2, -width / 2, length, width)
        windshield = QRectF(length * 0.06, -width * 0.36, length * 0.18, width * 0.72)
        rear_window = QRectF(-length * 0.36, -width * 0.32, length * 0.1, width * 0.64)
        radius = tile * 0.12
        headlight = tile * 0.045
        headlights = (
            QPointF(length / 2 - headlight * 1.2, -width / 2 + headlight * 1.8),
            QPointF(length / 2 - headlight * 1.2, width / 2 - headlight * 1.8),
        )
        shadow_color = QColor(0, 0, 0, 90)
        headlight_color = _qcolor(config.HEADLIGHT_COLOR)

        for car in cars:
            pose = poses[car]
            painter.save()
            painter.translate(ox + pose.x * tile, oy + pose.y * tile)

            painter.save()  # shadow always falls to the bottom right, whatever the car's angle
            painter.translate(tile * 0.04, tile * 0.06)
            painter.rotate(pose.angle)
            painter.setBrush(shadow_color)
            painter.drawRoundedRect(body, radius, radius)
            painter.restore()

            painter.rotate(pose.angle)
            color = _qcolor(config.CAR_COLORS[car.behavior.value])
            painter.setBrush(color)
            painter.drawRoundedRect(body, radius, radius)
            painter.setBrush(color.darker(180))
            painter.drawRoundedRect(windshield, radius / 2, radius / 2)
            painter.drawRoundedRect(rear_window, radius / 2, radius / 2)
            painter.setBrush(headlight_color)
            for point in headlights:
                painter.drawEllipse(point, headlight, headlight)
            painter.restore()

    def draw_hud(self, painter: QPainter, lines: list[str], opacity: float = 1.0) -> None:
        """Small info box in the top left corner."""
        if opacity <= 0 or not lines:
            return
        painter.save()
        painter.setOpacity(opacity)
        painter.setFont(self.hud_font)
        metrics = QFontMetrics(self.hud_font)
        padding = 8
        line_height = metrics.height()
        box_width = max(metrics.horizontalAdvance(line) for line in lines) + 2 * padding
        box_height = line_height * len(lines) + 2 * padding

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(*config.HUD_BACKGROUND))
        painter.drawRoundedRect(QRectF(10, 10, box_width, box_height), 6, 6)

        painter.setPen(QColor(*config.HUD_TEXT))
        for i, line in enumerate(lines):
            painter.drawText(QPointF(10 + padding, 10 + padding + metrics.ascent() + i * line_height), line)
        painter.restore()
