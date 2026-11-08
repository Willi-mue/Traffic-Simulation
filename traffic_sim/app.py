"""Main window: timers, input handling and wiring of simulation and renderer."""

from PySide6.QtCore import QElapsedTimer, QPoint, Qt, QTimer
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from . import config, i18n
from .animation import CarAnimator
from .car import StepResult
from .i18n import tr
from .renderer import Renderer
from .traffic import Traffic
from .world import World

HUD_FADE_MS = 500


class MainWindow(QWidget):
    def __init__(
        self,
        world: World,
        normal_cars: int = config.NORMAL_CARS,
        right_cars: int = config.RIGHT_CARS,
        seed: int | None = None,
    ):
        super().__init__()
        self.setWindowIcon(QIcon(str(config.ICON_PATH)))
        self.setWindowTitle(tr("window_title"))

        self.world = world
        self.normal_cars = normal_cars
        self.right_cars = right_cars
        self.seed = seed
        self.traffic = self.new_traffic()
        self.animator = CarAnimator()

        self.renderer = Renderer()
        self.show_lines = False
        self.show_help = False
        self.paused = False

        # view: tile size that fits the window, zoom on top of it, camera = map tile at the top left corner
        self.fit_tile = config.MIN_TILE_SIZE
        self.zoom = 1.0
        self.camera_x = 0.0
        self.camera_y = 0.0
        self._view_initialized = False
        self._map_cache: QPixmap | None = None
        self._map_cache_key = None
        self._drag_start: QPoint | None = None

        self.clock = QElapsedTimer()
        self.clock.start()
        self.hud_visible_until = config.HUD_SHOW_MS

        self.tick_interval = config.TICK_INTERVAL_MS
        self.frame_clock = QElapsedTimer()
        self.frame_clock.start()
        self.tick_timer = QTimer(self)
        self.tick_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start(self.tick_interval)

        self.frame_timer = QTimer(self)
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)  # Windows default is ~15.6 ms steps
        self.frame_timer.timeout.connect(self.update)
        self.frame_timer.start(config.FRAME_INTERVAL_MS)

        self.fit_to_screen()

    # ---- simulation ------------------------------------------------------

    def new_traffic(self) -> Traffic:
        return Traffic(self.world, self.normal_cars, self.right_cars, seed=self.seed)

    def tick(self) -> None:
        self.traffic.step()

    def set_tick_interval(self, interval: float) -> None:
        self.tick_interval = int(min(config.MAX_TICK_MS, max(config.MIN_TICK_MS, round(interval))))
        if not self.paused:
            self.tick_timer.start(self.tick_interval)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.tick_timer.stop()
        else:
            self.tick_timer.start(self.tick_interval)

    def restart(self) -> None:
        self.traffic = self.new_traffic()
        self.animator = CarAnimator()
        self.reset_view()

    def toggle_language(self) -> None:
        i18n.set_language(i18n.next_language())
        self.setWindowTitle(tr("window_title"))

    # ---- view ------------------------------------------------------------

    @property
    def tile_size(self) -> int:
        return max(2, round(self.fit_tile * self.zoom))

    @property
    def origin(self) -> tuple[int, int]:
        """Pixel position of the map's top left corner in the window."""
        tile = self.tile_size
        return round(-self.camera_x * tile), round(-self.camera_y * tile)

    def fit_to_screen(self) -> None:
        """Size the window so the whole map fits on the current screen and center it."""
        available = QApplication.primaryScreen().availableGeometry()
        tile = int(
            min(
                available.width() * config.SCREEN_FILL / self.world.width,
                available.height() * config.SCREEN_FILL / self.world.height,
            )
        )
        tile = max(config.MIN_TILE_SIZE, tile)
        self.setMinimumSize(self.world.width * config.MIN_TILE_SIZE, self.world.height * config.MIN_TILE_SIZE)
        self.resize(self.world.width * tile, self.world.height * tile)
        self.move(available.center() - self.rect().center())
        self.reset_view()

    def _update_fit_tile(self) -> None:
        self.fit_tile = max(1, min(self.width() // self.world.width, self.height() // self.world.height))

    def reset_view(self) -> None:
        """Zoom 1 and the map centered in the window."""
        self._update_fit_tile()
        self.zoom = 1.0
        tile = self.tile_size
        self.camera_x = -(self.width() / tile - self.world.width) / 2
        self.camera_y = -(self.height() / tile - self.world.height) / 2
        self._view_initialized = True

    def zoom_at(self, factor: float, px: float, py: float) -> None:
        """Zoom while keeping the map point under (px, py) in place."""
        old_tile = self.tile_size
        map_x = self.camera_x + px / old_tile
        map_y = self.camera_y + py / old_tile
        self.zoom = min(config.MAX_ZOOM, max(config.MIN_ZOOM, self.zoom * factor))
        new_tile = self.tile_size
        self.camera_x = map_x - px / new_tile
        self.camera_y = map_y - py / new_tile

    def map_pixmap(self) -> QPixmap:
        ox, oy = self.origin
        ratio = self.devicePixelRatioF()
        key = (self.tile_size, self.show_lines, ox, oy, self.width(), self.height(), ratio)
        if self._map_cache is None or self._map_cache_key != key:
            self._map_cache = self.renderer.render_map(
                self.world, self.tile_size, self.show_lines, ox, oy, self.width(), self.height(), ratio
            )
            self._map_cache_key = key
        return self._map_cache

    # ---- overlay ---------------------------------------------------------

    def show_hud(self) -> None:
        self.hud_visible_until = self.clock.elapsed() + config.HUD_SHOW_MS

    def hud_opacity(self) -> float:
        if self.paused or self.show_help:
            return 1.0
        remaining = self.hud_visible_until - self.clock.elapsed()
        return max(0.0, min(1.0, remaining / HUD_FADE_MS))

    def hud_lines(self) -> list[str]:
        state = tr("state_paused") if self.paused else tr("state_running")
        share = self.traffic.average_share
        lines = [
            tr("hud_tick", ms=self.tick_interval, state=state),
            tr("hud_cars", normal=self.normal_cars, right=self.right_cars),
            tr(
                "hud_stats",
                moving=share[StepResult.MOVED],
                waiting=share[StepResult.BLOCKED] + share[StepResult.LIGHT],
                light=share[StepResult.LIGHT],
            ),
            tr("hud_hint"),
        ]
        if self.show_help:
            lines += ["", *tr("help").splitlines()]
        return lines

    # ---- Qt events -------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        old = event.oldSize()
        if not self._view_initialized or old.width() <= 0 or old.height() <= 0:
            self.reset_view()
            return
        # keep zoom and the map point in the middle of the window
        old_tile = self.tile_size
        center_x = self.camera_x + old.width() / 2 / old_tile
        center_y = self.camera_y + old.height() / 2 / old_tile
        self._update_fit_tile()
        tile = self.tile_size
        self.camera_x = center_x - self.width() / 2 / tile
        self.camera_y = center_y - self.height() / 2 / tile

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.map_pixmap())

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tile = self.tile_size
        ox, oy = self.origin
        dt = self.frame_clock.restart() / 1000
        smooth_time = self.tick_interval / 1000 * config.ANIMATION_SMOOTHING
        poses = self.animator.update(self.traffic.cars, dt, smooth_time)
        self.renderer.draw_lights(painter, self.world, self.traffic.lights, tile, ox, oy)
        self.renderer.draw_cars(painter, self.traffic.cars, poses, tile, ox, oy)
        self.renderer.draw_hud(painter, self.hud_lines(), self.hud_opacity())
        painter.end()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_E:
            self.toggle_pause()
        elif key == Qt.Key.Key_W:
            self.set_tick_interval(self.tick_interval / config.TICK_SPEED_FACTOR)
        elif key == Qt.Key.Key_S:
            self.set_tick_interval(self.tick_interval * config.TICK_SPEED_FACTOR)
        elif key == Qt.Key.Key_Q:
            self.show_lines = not self.show_lines
        elif key == Qt.Key.Key_H:
            self.show_help = not self.show_help
        elif key == Qt.Key.Key_L:
            self.toggle_language()
        elif key == Qt.Key.Key_Right:
            self.camera_x -= 1
        elif key == Qt.Key.Key_Left:
            self.camera_x += 1
        elif key == Qt.Key.Key_Up:
            self.camera_y += 1
        elif key == Qt.Key.Key_Down:
            self.camera_y -= 1
        elif key == Qt.Key.Key_R:
            self.restart()
        elif key == Qt.Key.Key_Escape:
            self.close()
            return
        else:
            super().keyPressEvent(event)
            return
        self.show_hud()

    def wheelEvent(self, event):
        notches = event.angleDelta().y() / 120
        if notches:
            pos = event.position()
            self.zoom_at(config.ZOOM_STEP**notches, pos.x(), pos.y())

    def mousePressEvent(self, event):
        self._drag_start = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_start is None:
            return
        pos = event.position().toPoint()
        delta = pos - self._drag_start
        self._drag_start = pos
        self.camera_x -= delta.x() / self.tile_size
        self.camera_y -= delta.y() / self.tile_size

    def mouseReleaseEvent(self, event):
        self._drag_start = None
