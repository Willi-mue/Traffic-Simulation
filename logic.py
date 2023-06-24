import random


class All_cars:
    def __init__(self, street_file: str, normal: int, right_cars: int):
        self.normal_cars = normal
        self.right_cars = right_cars
        self.total_amount = self.normal_cars + self.right_cars

        self.street = self.get_street(street_file)
        self.all_cars = self.make_cars()

    def get_street(self, m_file: str):
        file = open(m_file, 'r')
        Lines = file.readlines()
        return Lines

    def make_cars(self):
        temp = []
        id = 0

        for _ in range(self.normal_cars):
            c = Car("normal", id, self.street)
            temp.append(c)
            id += 1

        for _ in range(self.right_cars):
            c = Car("right", id, self.street)
            temp.append(c)
            id += 1

        return temp


class Car:
    def __init__(self, behavior: str, id: int, street):
        self.id = id
        self.street = street
        self.behavior = behavior

        self.pos_x = None
        self.pos_y = None
        self.direction = None
        self.spawn()
        self.colour = self.get_color()

    def get_color(self):
        match self.behavior:
            case "normal":
                return [128, 0, 0]
            case "right":
                return [0, 128, 0]
            case _:
                print("Error in get_color")
                return [0, 0, 128]

    def spawn(self):
        x = None
        y = None

        while not self.check_tile(x, y):
            x = random.randint(0, len(self.street[0]) - 2)
            y = random.randint(0, len(self.street) - 1)

        self.pos_x = x
        self.pos_y = y

        self.get_tile()

    def check_tile(self, x, y):
        if x is None and y is None:
            return False
        if self.street[y][x] == ">" or self.street[y][x] == "v" or self.street[y][x] == "^" or self.street[y][x] == "<":
            return True
        else:
            return False

    def get_tile(self):
        match self.street[self.pos_y][self.pos_x]:
            case ">":
                direction = "right"
            case "<":
                direction = "left"
            case "^":
                direction = "up"
            case "v":
                direction = "down"
            case ".":
                match self.behavior:
                    case "right":
                        direction = self.go_right()
                    case _:
                        direction = self.go_random()
            case _:
                direction = None
                print("Error in get_tile")

        self.direction = direction

    def drive(self, auto_list: list, ampel_setting: bool, slow_down: float = 0.8):
        test1 = self.check_front(auto_list)
        test2 = self.check_ampel(ampel_setting)
        test3 = random.random() < slow_down

        if test1 and test2 and test3:
            if self.direction == "left":
                self.pos_x -= 1
            elif self.direction == "right":
                self.pos_x += 1
            elif self.direction == "up":
                self.pos_y -= 1
            elif self.direction == "down":
                self.pos_y += 1

    def check_front(self, auto_list) -> bool:
        for auto in auto_list:

            if auto.id == self.id:
                continue
            else:
                match auto.direction:
                    case "left":
                        if self.pos_x - 1 == auto.pos_x and auto.pos_y == self.pos_y:
                            return False

                    case "right":
                        if self.pos_x + 1 == auto.pos_x and auto.pos_y == self.pos_y:
                            return False

                    case "up":
                        if auto.pos_x == self.pos_x and self.pos_y - 1 == auto.pos_y:
                            return False

                    case "down":
                        if auto.pos_x == self.pos_x and self.pos_y + 1 == auto.pos_y:
                            return False
                    case _:
                        print("Error in check_front")
                        return False

        return True

    def check_ampel(self, ampel_setting: bool) -> bool:
        # True =  oben unten || False = links rechts
        if self.direction == "up" and self.street[self.pos_y - 2][self.pos_x - 2] == "T" and ampel_setting:
            return False
        elif self.direction == "down" and self.street[self.pos_y + 2][self.pos_x + 2] == "T" and ampel_setting:
            return False
        elif self.direction == "left" and self.street[self.pos_y + 1][self.pos_x - 4] == "T" and not ampel_setting:
            return False
        elif self.direction == "right" and self.street[self.pos_y - 1][self.pos_x + 4] == "T" and not ampel_setting:
            return False

        return True

    def go_random(self):
        check = []

        match self.direction:
            case "up":
                if self.street[self.pos_y][self.pos_x + 1] == ">":
                    check.append("right")
                if self.street[self.pos_y - 1][self.pos_x] == "^":
                    check.append("up")
                if self.street[self.pos_y][self.pos_x - 1] == "<":
                    check.append("left")
            case "down":
                if self.street[self.pos_y][self.pos_x - 1] == "<":
                    check.append("left")
                if self.street[self.pos_y + 1][self.pos_x] == "v":
                    check.append("down")
                if self.street[self.pos_y][self.pos_x + 1] == ">":
                    check.append("right")
            case "left":
                if self.street[self.pos_y - 1][self.pos_x] == "^":
                    check.append("up")
                if self.street[self.pos_y][self.pos_x - 1] == "<":
                    check.append("left")
                if self.street[self.pos_y + 1][self.pos_x] == "v":
                    check.append("down")
            case "right":
                if self.street[self.pos_y + 1][self.pos_x] == "v":
                    check.append("down")
                if self.street[self.pos_y][self.pos_x + 1] == ">":
                    check.append("right")
                if self.street[self.pos_y - 1][self.pos_x] == "^":
                    check.append("up")
            case _:
                print("Error in go_random")

        r = random.randint(0, len(check) - 1)

        return check[r]

    def go_right(self):
        match self.direction:
            case "up":
                if self.street[self.pos_y][self.pos_x + 1] == ">":
                    return "right"
                elif self.street[self.pos_y - 1][self.pos_x] == "^":
                    return "up"
                elif self.street[self.pos_y][self.pos_x - 1] == "<":
                    return "left"
            case "down":
                if self.street[self.pos_y][self.pos_x - 1] == "<":
                    return "left"
                elif self.street[self.pos_y + 1][self.pos_x] == "v":
                    return "down"
                elif self.street[self.pos_y][self.pos_x + 1] == ">":
                    return "right"
            case "left":
                if self.street[self.pos_y - 1][self.pos_x] == "^":
                    return "up"
                elif self.street[self.pos_y][self.pos_x - 1] == "<":
                    return "left"
                elif self.street[self.pos_y + 1][self.pos_x] == "v":
                    return "down"
            case "right":
                if self.street[self.pos_y + 1][self.pos_x] == "v":
                    return "down"
                elif self.street[self.pos_y][self.pos_x + 1] == ">":
                    return "right"
                elif self.street[self.pos_y - 1][self.pos_x] == "^":
                    return "up"
            case _:
                print("Error in go_right")
                return None
