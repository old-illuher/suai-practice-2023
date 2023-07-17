from station import Station
from datetime import time


class Route:
    name: str
    startingPoint: Station
    endingPoint: Station
    stoppingPoints: list
    distance: int

    def __init__(self, data, startingPoint, endingPoint):
        self.name = data['name']
        self.startingPoint = startingPoint
        self.endingPoint = endingPoint
        self.distance = data['distance']
        self.stoppingPoints = []
        for point in data['stoppingPoints']:
            self.stoppingPoints.append(StoppingPoint(point, self))


class StoppingPoint:
    route: Route
    openTime: time
    closeTime: time
    distance: float

    def __init__(self, data, route):
        self.route = route
        self.openTime = time.fromisoformat(data['openTime'])
        self.closeTime = time.fromisoformat(data['closeTime'])
        self.distance = data['distance']
