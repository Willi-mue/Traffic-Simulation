import sys
import ctypes

from logic import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class main_application(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("bilder/icon.png"))
        # Setzen des Icons
        my_app_id = 'by_Müller_Willi.Verkehrs_Simulation.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

        self.setWindowTitle('Verkehrs_Simulation')

        self.hoehe = 1080
        self.breite = 1920

        self.resize(self.breite, self.hoehe)
        self.setMinimumSize(self.breite, self.hoehe)

        self.sim = QLabel(self)
        self.figures = QLabel(self)

        self.show_line = False
        self.stop = False
        self.tile_size = 20
        self.ampel_cords = []
        
        self.ampel_swap = True
        self.ampel_swap_rate = 32

        self.count_time = 0

        # refactore
        self.cars = {}
        make_cars(self.cars, anzahl=80, right_cars=25)
        # self.cars = All_cars(amount = 80, right_cars = 25, trucks = 2)



        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animation)
        self.speed = 100
        self.timer.start(self.speed)

        self.setWindowTitle(str(self.speed))

        self.links_oben = QImage("bilder/links_oben.png")
        self.rechts_oben = QImage("bilder/rechts_oben.png")
        self.links_unten = QImage("bilder/links_unten.png")
        self.rechts_unten = QImage("bilder/rechts_unten.png")
        self.horizontal = QImage("bilder/horizontal.png")
        self.vertikal = QImage("bilder/vertikal.png")

        self.ampel1 = QImage("bilder/ampel_1.png")
        self.ampel2 = QImage("bilder/ampel_2.png")

        self.up = QImage("bilder/up.png")
        self.down = QImage("bilder/down.png")
        self.left = QImage("bilder/left.png")
        self.right = QImage("bilder/right.png")
        self.point = QImage("bilder/point.png")

        self.first_draw()

    def first_draw(self):
        canvas = QPixmap(self.breite, self.hoehe)
        canvas.fill(Qt.black)
        self.sim.setPixmap(canvas)
        self.sim.setGeometry(0, 0, self.breite, self.hoehe)

        pen = QPen()
        pen.setWidth(2)
        pen.setColor(Qt.black)

        painter_sim = QPainter(self.sim.pixmap())

        for i in range(len(karte)):
            for j in range(len(karte[i])):
                if karte[i][j] == "-":
                    painter_sim.drawImage(QRect((j * self.tile_size), (i * self.tile_size),
                                                self.tile_size, self.tile_size), self.horizontal)
                elif karte[i][j] == "|":
                    painter_sim.drawImage(QRect((j * self.tile_size), (i * self.tile_size),
                                                self.tile_size, self.tile_size), self.vertikal)
                elif karte[i][j] == "T":
                    self.ampel_cords.append([i, j])

                elif karte[i][j] == "a":
                    painter_sim.drawImage(QRect((j * self.tile_size), (i * self.tile_size),
                                                self.tile_size, self.tile_size), self.links_oben)
                elif karte[i][j] == "b":
                    painter_sim.drawImage(QRect((j * self.tile_size), (i * self.tile_size),
                                                self.tile_size, self.tile_size), self.rechts_oben)
                elif karte[i][j] == "c":
                    painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                self.tile_size, self.tile_size), self.links_unten)
                elif karte[i][j] == "d":
                    painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                self.tile_size, self.tile_size), self.rechts_unten)

                if self.show_line:
                    if karte[i][j] == ">":
                        painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                    self.tile_size, self.tile_size), self.right)
                    elif karte[i][j] == "<":
                        painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                    self.tile_size, self.tile_size), self.left)
                    elif karte[i][j] == "v":
                        painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                    self.tile_size, self.tile_size), self.down)
                    elif karte[i][j] == "^":
                        painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                    self.tile_size, self.tile_size), self.up)
                    elif karte[i][j] == ".":
                        painter_sim.drawImage(QRect(j * self.tile_size, i * self.tile_size,
                                                    self.tile_size, self.tile_size), self.point)

    def animation(self):

        self.setWindowTitle(str(self.speed))

        if self.count_time % self.ampel_swap_rate == 0 or self.count_time == 0:
            if self.ampel_swap:
                self.ampel_swap = False
            else:
                self.ampel_swap = True

        self.count_time += 1

        # draw cars
        for key in self.cars:
            self.cars[key].look_under()
            self.cars[key].drive(key, self.cars, self.ampel_swap)

        self.update()

    def paintEvent(self, event):
        self.setWindowTitle(str(self.speed))
        canvas = QPixmap(self.breite, self.hoehe)
        canvas.fill(QColor(0, 0, 0, 0))
        self.figures.setPixmap(canvas)
        self.figures.setGeometry(0, 0, self.breite, self.hoehe)

        painter_figures = QPainter(self.figures.pixmap())

        if self.ampel_swap:
            for i in self.ampel_cords:
                painter_figures.drawImage(QRect((i[1] * self.tile_size), (i[0] * self.tile_size),
                                                self.tile_size, self.tile_size), self.ampel1)
        else:
            for i in self.ampel_cords:
                painter_figures.drawImage(QRect((i[1] * self.tile_size), (i[0] * self.tile_size),
                                                self.tile_size, self.tile_size), self.ampel2)

        for key in self.cars:
            painter_figures.fillRect(QRect(self.cars[key].pos_x * self.tile_size + self.tile_size // 4,
                                           self.cars[key].pos_y * self.tile_size + self.tile_size // 4,
                                           self.tile_size // 2, self.tile_size // 2),
                                     QColor(self.cars[key].colour[0], self.cars[key].colour[1],
                                            self.cars[key].colour[2]))

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_P:
            if not self.stop:
                self.timer.stop()
                self.stop = True
            else:
                self.stop = False
                self.timer.start(self.speed)

        if key == Qt.Key_E:
            self.speed += 1
            if not self.stop:
                self.timer.start(self.speed)
            self.update()

        if key == Qt.Key_W:
            if self.speed - 1 >= 0:
                self.speed -= 1
            if not self.stop:
                self.timer.start(self.speed)
            self.update()

        if key == Qt.Key_Q:
            if not self.show_line:
                self.show_line = True
                self.first_draw()
                self.update()
            else:
                self.show_line = False
                self.first_draw()
                self.update()

        if key == Qt.Key_R:
            make_cars(self.cars, anzahl=80, right_cars=25)

        if key == Qt.Key_Escape:
            sys.exit()


def main():
    app = QApplication(sys.argv)
    application = main_application()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
