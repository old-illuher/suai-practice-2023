from route import Route
from station import Station


class Train():
    name: str
    type: str   # тип состава: моделируемый/немоделируемый
    maxCap: float   # максимальный объем
    curCap: float   # текущий объем
    speed: float = 0.0   # скорость движения км/ч
    route: Route    # маршрут, по которому ездит состав
    distanceTravelled: float = 0.0
    lastStation: Station    # последняя посещенная точка
    state: str  # состояние: погрузка/выгрузка/ожидание/движение

    def __init__(self, data, route, lastStation, state, routeList):
        self.name = data['name']
        self.type = data['type']
        self.maxCap = data['maxCap']
        self.curCap = data['curCap']
        self.speed = data.get('speed', 0.0)
        self.distanceTravelled = data.get('distanceTravelled', 0.0)
        self.route = route
        self.routeList = routeList
        self.lastStation = lastStation
        self.state = state

    def load(self, val):
        self.curCap += val

    def unload(self, val):
        self.curCap -= val

    def move(self):
        self.distanceTravelled += self.speed
        if self.distanceTravelled >= self.route.distance:
            self.state = 'WAITING'

            if self.lastStation == self.route.startingPoint:
                self.lastStation = self.route.endingPoint
            else:
                self.lastStation = self.route.startingPoint
            self.distanceTravelled = 0
            self.lastStation.trainQueue.append(self)

            if (len(self.routeList) > 1) & (self.lastStation == self.route.endingPoint):
                # проверка на существование такого маршрута
                if self.routeList.index(self.route) == len(self.routeList)-1:
                    self.routeList = self.routeList[::-1]
                self.route = self.routeList[self.routeList.index(self.route)+1]

            return False
        return True
