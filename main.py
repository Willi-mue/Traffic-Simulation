import sys
import ctypes

from logic import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class main_application(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("assets/icon.png"))
        # Setzen des Icons
        my_app_id = 'by_Müller_Willi.Verkehrs_Simulation.1.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

        self.setWindowTitle('Verkehrs_Simulation')

        self.scale = 1.5

        self.height = int(1080 * self.scale)
        self.width = int(1920 * self.scale)

        self.resize(self.width, self.height)
        self.setMinimumSize(self.width, self.height)

        self.sim = QLabel(self)
        self.figures = QLabel(self)

        self.show_line = False
        self.stop = False
        self.tile_size = int(self.width * 1 / 96)
        self.ampel_cords = []

        self.ampel_swap = True
        self.ampel_swap_rate = 32

        self.count_time = 0

        self.cars = All_cars('maps/map1.txt', normal=30, right_cars=20)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animation)
        self.speed = 100
        self.timer.start(self.speed)

        self.setWindowTitle(str(self.speed))

        self.pics = {
            "links_oben": QImage("assets/links_oben.png"),
            "rechts_oben": QImage("assets/rechts_oben.png"),
            "links_unten": QImage("assets/links_unten.png"),
            "rechts_unten": QImage("assets/rechts_unten.png"),
            "horizontal": QImage("assets/horizontal.png"),
            "vertikal": QImage("assets/vertikal.png"),
            "ampel1": QImage("assets/ampel_1.png"),
            "ampel2": QImage("assets/ampel_2.png"),
            "up": QImage("assets/up.png"),
            "down": QImage("assets/down.png"),
            "left": QImage("assets/left.png"),
            "right": QImage("assets/right.png"),
            "point": QImage("assets/point.png"),
        }

        self.first_draw()

    def first_draw(self):
        canvas = QPixmap(self.width, self.height)
        canvas.fill(Qt.black)
        self.sim.setPixmap(canvas)
        self.sim.setGeometry(0, 0, self.width, self.height)

        painter_sim = QPainter(self.sim.pixmap())

        for y, i in enumerate(self.cars.street):
            for x, j in enumerate(i):
                match j:
                    case "-":
                        painter_sim.drawImage(QRect((x * self.tile_size), (y * self.tile_size),
                                                    self.tile_size, self.tile_size), self.pics["horizontal"])
                    case "|":
                        painter_sim.drawImage(QRect((x * self.tile_size), (y * self.tile_size),
                                                    self.tile_size, self.tile_size), self.pics["vertikal"])
                    case "T":
                        self.ampel_cords.append([y, x])

                    case "a":
                        painter_sim.drawImage(QRect((x * self.tile_size), (y * self.tile_size),
                                                    self.tile_size, self.tile_size), self.pics["links_oben"])
                    case "b":
                        painter_sim.drawImage(QRect((x * self.tile_size), (y * self.tile_size),
                                                    self.tile_size, self.tile_size), self.pics["rechts_oben"])
                    case "c":
                        painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                    self.tile_size, self.tile_size), self.pics["links_unten"])
                    case "d":
                        painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                    self.tile_size, self.tile_size), self.pics["rechts_unten"])
                    case _:
                        pass

                if self.show_line:
                    match j:
                        case ">":
                            painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                        self.tile_size, self.tile_size), self.pics["right"])
                        case "<":
                            painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                        self.tile_size, self.tile_size), self.pics["left"])
                        case "v":
                            painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                        self.tile_size, self.tile_size), self.pics["down"])
                        case "^":
                            painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                        self.tile_size, self.tile_size), self.pics["up"])
                        case ".":
                            painter_sim.drawImage(QRect(x * self.tile_size, y * self.tile_size,
                                                        self.tile_size, self.tile_size), self.pics["point"])
                        case _:
                            pass

    def animation(self):

        self.setWindowTitle(str(self.speed))

        if self.count_time % self.ampel_swap_rate == 0 or self.count_time == 0:
            if self.ampel_swap:
                self.ampel_swap = False
            else:
                self.ampel_swap = True

        self.count_time += 1

        for auto in self.cars.all_cars:
            auto.get_tile()
            auto.drive(auto_list=self.cars.all_cars, ampel_setting=self.ampel_swap)

        self.update()

    def paintEvent(self, event):
        self.setWindowTitle(str(self.speed))
        canvas = QPixmap(self.width, self.height)
        canvas.fill(QColor(0, 0, 0, 0))
        self.figures.setPixmap(canvas)
        self.figures.setGeometry(0, 0, self.width, self.height)

        painter_figures = QPainter(self.figures.pixmap())

        if self.ampel_swap:
            for i in self.ampel_cords:
                painter_figures.drawImage(QRect((i[1] * self.tile_size), (i[0] * self.tile_size),
                                                self.tile_size, self.tile_size), self.pics["ampel1"])
        else:
            for i in self.ampel_cords:
                painter_figures.drawImage(QRect((i[1] * self.tile_size), (i[0] * self.tile_size),
                                                self.tile_size, self.tile_size), self.pics["ampel2"])

        for auto in self.cars.all_cars:
            painter_figures.fillRect(QRect(auto.pos_x * self.tile_size + self.tile_size // 4,
                                           auto.pos_y * self.tile_size + self.tile_size // 4,
                                           self.tile_size // 2, self.tile_size // 2),
                                     QColor(auto.colour[0], auto.colour[1], auto.colour[2]))

    def keyPressEvent(self, event):
        key = event.key()

        # stop sim
        if key == Qt.Key_E:
            if not self.stop:
                self.timer.stop()
                self.stop = True
            else:
                self.stop = False
                self.timer.start(self.speed)

        # speedup sim
        if key == Qt.Key_W:
            self.speed += 1
            if not self.stop:
                self.timer.start(self.speed)
            self.update()

        # speeddown sim
        if key == Qt.Key_S:
            if self.speed - 1 >= 0:
                self.speed -= 1
            if not self.stop:
                self.timer.start(self.speed)
            self.update()

        # show direction lines
        if key == Qt.Key_Q:
            if not self.show_line:
                self.show_line = True
                self.first_draw()
                self.update()
            else:
                self.show_line = False
                self.first_draw()
                self.update()

        # reset
        if key == Qt.Key_R:
            self.cars = All_cars('maps/map1.txt', normal=30, right_cars=20)

        # exit
        if key == Qt.Key_Escape:
            sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    application = main_application()
    application.show()
    sys.exit(app.exec_())
