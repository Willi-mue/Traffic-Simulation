"""Central place for all tunable values."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ASSET_DIR = PACKAGE_DIR / "assets"
ICON_PATH = ASSET_DIR / "ui" / "icon.jpg"
MAP_DIR = PACKAGE_DIR / "maps"
DEFAULT_MAP = MAP_DIR / "map1.txt"

# Window
APP_USER_MODEL_ID = "WilliMueller.TrafficSimulation"  # Windows taskbar grouping and icon
SCREEN_FILL = 0.9  # share of the free screen area the window may use at start
MIN_TILE_SIZE = 4  # pixels; limits how small the window can be made
FRAME_INTERVAL_MS = 16  # ~60 frames per second for smooth movement
ANIMATION_SMOOTHING = 0.8  # how softly drawn cars follow the simulation, in simulation ticks
MIN_ZOOM = 0.5
MAX_ZOOM = 6.0
ZOOM_STEP = 1.15  # per mouse wheel notch

# Simulation
NORMAL_CARS = 30
RIGHT_CARS = 20
TICK_INTERVAL_MS = 100
MIN_TICK_MS = 20
MAX_TICK_MS = 1000
TICK_SPEED_FACTOR = 1.25  # W/S change the tick interval by this factor
LIGHT_SWITCH_INTERVAL = 32  # ticks one axis keeps green + yellow before the other axis gets green
LIGHT_YELLOW_TICKS = 4  # last ticks of each green phase are yellow
LIGHT_OFFSET_STEP = 16  # phase shift between consecutive traffic lights, in ticks
MOVE_PROBABILITY = 0.8  # chance that a car moves in a tick when the way is free
MAX_INTERSECTION_SIZE = 4  # max distance between '.' tiles of the same intersection

# Colors (RGB)
BACKGROUND_COLOR = (38, 56, 42)  # grass between the roads
ROAD_COLOR = (64, 67, 72)  # asphalt
CURB_COLOR = (200, 204, 208)  # road edges
MARKING_COLOR = (225, 225, 225)  # dashed lines between lanes and stop lines
GUIDE_COLOR = (150, 155, 160)  # direction arrows (Q)
CAR_COLORS = {
    "normal": (220, 70, 70),
    "right": (70, 190, 110),
}
HEADLIGHT_COLOR = (255, 240, 190)
LIGHT_RED = (240, 60, 55)
LIGHT_YELLOW = (245, 200, 40)
LIGHT_GREEN = (70, 220, 100)
LIGHT_HOUSING = (24, 26, 29)
HUD_BACKGROUND = (20, 20, 20, 215)
HUD_TEXT = (235, 235, 235)
HUD_SHOW_MS = 4000  # overlay hides after this time without input (stays while paused or help is open)
STATS_SMOOTHING = 0.05  # weight of the newest tick in the moving average of the overlay statistics
