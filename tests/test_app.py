import pytest
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from traffic_sim import config
from traffic_sim.animation import interpolate_angle
from traffic_sim.app import MainWindow
from traffic_sim.world import World


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp):
    world = World.from_file(config.MAP_DIR / "map1.txt")
    win = MainWindow(world, normal_cars=10, right_cars=5, seed=1)
    win.resize(930, 420)
    win.show()
    qapp.processEvents()
    yield win
    win.close()


def press(win, key):
    win.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))


def test_speed_keys_and_limits(window):
    start = window.tick_interval
    press(window, Qt.Key.Key_W)
    assert window.tick_interval < start
    for _ in range(50):
        press(window, Qt.Key.Key_W)
    assert window.tick_interval == config.MIN_TICK_MS
    for _ in range(50):
        press(window, Qt.Key.Key_S)
    assert window.tick_interval == config.MAX_TICK_MS


def test_pause_stops_simulation(window):
    press(window, Qt.Key.Key_E)
    assert window.paused and not window.tick_timer.isActive()
    press(window, Qt.Key.Key_E)
    assert not window.paused and window.tick_timer.isActive()


def test_restart_resets_everything(window):
    for _ in range(20):
        window.tick()
    window.zoom_at(2, 100, 100)
    press(window, Qt.Key.Key_R)
    assert window.traffic.tick_count == 0
    assert window.zoom == 1.0


def test_escape_closes(window, qapp):
    press(window, Qt.Key.Key_Escape)
    qapp.processEvents()
    assert not window.isVisible()


def test_zoom_keeps_point_under_cursor(window):
    px, py = 300, 200
    before = (window.camera_x + px / window.tile_size, window.camera_y + py / window.tile_size)
    window.zoom_at(2.0, px, py)
    after = (window.camera_x + px / window.tile_size, window.camera_y + py / window.tile_size)
    assert after == pytest.approx(before)
    assert window.zoom == 2.0


def test_zoom_is_limited(window):
    for _ in range(100):
        window.zoom_at(2, 0, 0)
    assert window.zoom == config.MAX_ZOOM


def test_resize_keeps_zoom_and_center(window, qapp):
    window.zoom_at(2.0, 465, 210)
    old_size = window.size()
    center_before = (
        window.camera_x + old_size.width() / 2 / window.tile_size,
        window.camera_y + old_size.height() / 2 / window.tile_size,
    )
    window.resize(QSize(1200, 600))
    qapp.processEvents()
    center_after = (
        window.camera_x + window.width() / 2 / window.tile_size,
        window.camera_y + window.height() / 2 / window.tile_size,
    )
    assert window.zoom == 2.0
    assert center_after == pytest.approx(center_before)


def test_whole_map_visible_at_start(qapp):
    world = World.from_file(config.MAP_DIR / "small.txt")
    win = MainWindow(world, normal_cars=5, right_cars=5)
    win.show()
    qapp.processEvents()
    ox, oy = win.origin
    assert ox >= 0 and oy >= 0
    assert ox + world.width * win.tile_size <= win.width()
    assert oy + world.height * win.tile_size <= win.height()
    win.close()


def test_hud_hides_and_comes_back(window):
    window.hud_visible_until = window.clock.elapsed() - 10_000
    assert window.hud_opacity() == 0
    press(window, Qt.Key.Key_Q)
    assert window.hud_opacity() == 1
    window.hud_visible_until = window.clock.elapsed() - 10_000
    press(window, Qt.Key.Key_H)
    assert window.hud_opacity() == 1  # help stays visible


def test_painting_works_with_lines_and_zoom(window):
    for _ in range(5):
        window.tick()
    press(window, Qt.Key.Key_Q)
    window.zoom_at(config.MAX_ZOOM, 400, 200)
    image = window.grab().toImage()
    assert not image.isNull()
    assert image.size() == window.size()


def test_language_key_switches_overlay_and_title(window):
    assert window.windowTitle() == "Verkehrssimulation"
    assert any("Autos" in line for line in window.hud_lines())
    press(window, Qt.Key.Key_L)
    assert window.windowTitle() == "Traffic Simulation"
    assert any("Cars" in line for line in window.hud_lines())
    press(window, Qt.Key.Key_H)
    assert any("switch language" in line for line in window.hud_lines())


def test_interpolate_angle_takes_short_way():
    assert interpolate_angle(270, 0, 0.5) == pytest.approx(315)
    assert interpolate_angle(0, 270, 0.5) == pytest.approx(-45)
    assert interpolate_angle(90, 180, 1.0) == pytest.approx(180)
