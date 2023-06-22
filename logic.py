import random


def read_map():
    file = open('maps/map1.txt', 'r')
    Lines = file.readlines()
    return Lines

#refactor
karte = read_map()

def slow(effekt=80):
    n = random.randint(0, effekt)
    if n == effekt//2:
        return False
    return True


def make_cars(autos: dict, anzahl=10, right_cars=0):
    for i in range(anzahl):
        if right_cars > 0:
            autos[str(i)] = auto(colour=[0, 150, 0])
            right_cars -= 1
            autos[str(i)].right()

        else:
            autos[str(i)] = auto(colour=[150, 0, 0])

        autos[str(i)].spawn()


def check_ampel(direction, x, y, setting):
    # True =  oben unten || False = links rechts
    if direction == "up" and karte[y - 2][x - 2] == "T" and setting:
        return False
    elif direction == "down" and karte[y + 2][x + 2] == "T" and setting:
        return False
    elif direction == "left" and karte[y + 1][x - 4] == "T" and not setting:
        return False
    elif direction == "right" and karte[y - 1][x + 4] == "T" and not setting:
        return False

    return True


def check_car_front(aktueller_key, autos: dict):
    for key in autos:
        if aktueller_key == key:
            pass
        else:
            if autos[aktueller_key].direction == "left":
                if autos[aktueller_key].pos_x - 1 == autos[key].pos_x and \
                        autos[aktueller_key].pos_y == autos[key].pos_y:
                    return False

            elif autos[aktueller_key].direction == "right":
                if autos[aktueller_key].pos_x + 1 == autos[key].pos_x and \
                        autos[aktueller_key].pos_y == autos[key].pos_y:
                    return False

            elif autos[aktueller_key].direction == "up":
                if autos[aktueller_key].pos_x == autos[key].pos_x and \
                        autos[aktueller_key].pos_y - 1 == autos[key].pos_y:
                    return False

            elif autos[aktueller_key].direction == "down":
                if autos[aktueller_key].pos_x == autos[key].pos_x and \
                        autos[aktueller_key].pos_y + 1 == autos[key].pos_y:
                    return False

    return True





def abbiegen_random(x, y, direction):
    check = []
    if direction == "up":
        if karte[y][x + 1] == ">":
            check.append("right")
        if karte[y - 1][x] == "^":
            check.append("up")
        if karte[y][x - 1] == "<":
            check.append("left")
    elif direction == "down":
        if karte[y][x - 1] == "<":
            check.append("left")
        if karte[y + 1][x] == "v":
            check.append("down")
        if karte[y][x + 1] == ">":
            check.append("right")
    elif direction == "left":
        if karte[y - 1][x] == "^":
            check.append("up")
        if karte[y][x - 1] == "<":
            check.append("left")
        if karte[y + 1][x] == "v":
            check.append("down")
    elif direction == "right":
        if karte[y + 1][x] == "v":
            check.append("down")
        if karte[y][x + 1] == ">":
            check.append("right")
        if karte[y - 1][x] == "^":
            check.append("up")

    rand = random.randint(0, len(check) - 1)

    return check[rand]


def abbiegen_immer_rechts(x, y, direction):
    if direction == "up":
        if karte[y][x + 1] == ">":
            return "right"
        elif karte[y - 1][x] == "^":
            return "up"
        elif karte[y][x - 1] == "<":
            return "left"
    elif direction == "down":
        if karte[y][x - 1] == "<":
            return "left"
        elif karte[y + 1][x] == "v":
            return "down"
        elif karte[y][x + 1] == ">":
            return "right"
    elif direction == "left":
        if karte[y - 1][x] == "^":
            return "up"
        elif karte[y][x - 1] == "<":
            return "left"
        elif karte[y + 1][x] == "v":
            return "down"
    elif direction == "right":
        if karte[y + 1][x] == "v":
            return "down"
        elif karte[y][x + 1] == ">":
            return "right"
        elif karte[y - 1][x] == "^":
            return "up"


class auto:
    def __init__(self, colour):
        self.direction = None
        self.pos_x = None
        self.pos_y = None
        self.map = karte
        self.right_car = False
        self.colour = colour

    def drive(self, key, autos: dict, ampel_setting):
        test1 = check_car_front(key, autos)
        test2 = check_ampel(self.direction, self.pos_x, self.pos_y, ampel_setting)
        test3 = slow()
        if test1 and test2 and test3:
            if self.direction == "left":
                self.pos_x -= 1
            elif self.direction == "right":
                self.pos_x += 1
            elif self.direction == "up":
                self.pos_y -= 1
            elif self.direction == "down":
                self.pos_y += 1

    def right(self):
        self.right_car = True

    def look_under(self):
        if self.map[self.pos_y][self.pos_x] == ">":
            direction = "right"
        elif self.map[self.pos_y][self.pos_x] == "<":
            direction = "left"
        elif self.map[self.pos_y][self.pos_x] == "^":
            direction = "up"
        elif self.map[self.pos_y][self.pos_x] == "v":
            direction = "down"
        elif self.map[self.pos_y][self.pos_x] == ".":
            if self.right_car:
                direction = abbiegen_immer_rechts(self.pos_x, self.pos_y, self.direction)
            else:
                direction = abbiegen_random(self.pos_x, self.pos_y, self.direction)
        else:
            direction = None
            print("Error in look_under")

        self.direction = direction

    def spawn(self, x=None, y=None):
        while not self.check_tile(x, y):
            x = random.randint(0, len(self.map[0]) - 2)
            y = random.randint(0, len(self.map) - 1)

        self.pos_x = x
        self.pos_y = y
        self.look_under()

    def check_tile(self, x, y):
        if x is None and y is None:
            return False
        if self.map[y][x] == ">" or self.map[y][x] == "v" or self.map[y][x] == "^" or self.map[y][x] == "<":
            return True
        else:
            return False
