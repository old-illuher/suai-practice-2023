import mysql.connector
import json

from station import Station, Terminal, TransshipmentPoint
from train import Train
from route import Route
from datetime import datetime
from datetime import timedelta
import copy


def calculate_train_arrival_time(baseTrain: Train, currentTime: datetime):
    train = copy.deepcopy(baseTrain)
    res = True
    while res:
        currentTime += timedelta(hours=1)
        if train.state == 'MOVING':
            shouldMove = True
            if train.route.stoppingPoints:
                if train.lastStation == train.route.startingPoint:
                    for point in train.route.stoppingPoints:
                        if (train.distanceTravelled + train.speed > point.distance) & (
                                train.distanceTravelled <= point.distance):
                            if not (point.openTime <= currentTime <= point.closeTime):
                                if train.distanceTravelled != point.distance:
                                    train.distanceTravelled = point.distance
                                shouldMove = False
                else:
                    for point in reversed(train.route.stoppingPoints):
                        if (train.distanceTravelled + train.speed > train.route.distance - point.distance) & (
                                train.distanceTravelled <= train.route.distance - point.distance):
                            if not (point.openTime <= currentTime <= point.closeTime):
                                if train.distanceTravelled != train.route.distance - point.distance:
                                    train.distanceTravelled = train.route.distance - point.distance
                                shouldMove = False
            if shouldMove:
                res = train.move()
    return currentTime


def find_station_by_name(station_list, station_name):
    for station in station_list:
        if station.name == station_name:
            return station
    return None


def find_route_by_name(route_list, route_name):
    for route in route_list:
        if route.name == route_name:
            return route
    return None


def model(data):

    stations_list = []
    routes_list = []
    trains_list = []

    startDate = data['startDate']
    endDate = data['endDate']

    startTime = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    endTime = datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')

    discreteness = data['discreteness']

    modeling_time = (endTime - startTime).total_seconds() / discreteness

    print(modeling_time)

    stations = data['stations']
    routes = data['routes']
    trains = data['trains']

    for station in stations:
        if station['type'] == 'TERMINAL':
            stations_list.append(Terminal(station))
        else:
            stations_list.append(TransshipmentPoint(station))
        print(stations_list[-1].__dict__)

    for route in routes:
        startingPoint = find_station_by_name(stations_list, route['startingPoint'])
        endingPoint = find_station_by_name(stations_list, route['endingPoint'])
        routes_list.append(Route(route, startingPoint, endingPoint))
        print(routes_list[-1].__dict__)

    for train in trains:
        if train['type'] == 'MODEL':
            route = find_route_by_name(routes_list, train['route'])
            routeList = []
            for routeName in train['routeList']:
                routeList.append(find_route_by_name(routes_list, routeName))
            lastStation = find_station_by_name(stations_list, train['lastStation'])
            if ((lastStation.type == 'TERMINAL') & (train['curCap'] == 0)) | ((lastStation.type == 'TRANSSHIPMENT') & (train['curCap'] == train['maxCap'])):
                train_object = Train(train, route, lastStation, 'WAITING', routeList)
                lastStation.trainQueue.append(train_object)
            elif ((lastStation.type == 'TERMINAL') & (train['curCap'] > 0)) | ((lastStation.type == 'TRANSSHIPMENT') & (train['curCap'] == 0)):
                train_object = Train(train, route, lastStation, 'MOVING', routeList)
            trains_list.append(train_object)
        else:
            transshipmentPoint = find_station_by_name(stations_list, train['transshipmentPoint'])
            train_object = Train(train, None, transshipmentPoint, 'WAITING', None)
            find_station_by_name(stations_list, train['transshipmentPoint']).transshipmentTrains.append(train_object)
        print(trains_list[-1].__dict__)

    connection_info = json.load(open('connection.json'))

    connection = mysql.connector.connect(
        host=connection_info['host'],
        user=connection_info['user'],
        password=connection_info['password'],
        database=connection_info['database']
    )

    cursor = connection.cursor()

    # работа модели
    for i in range(modeling_time.__int__()):

        currentTime = startTime.time()
        startTime += timedelta(hours=1)
        print(startTime)

        # добыча на терминалах
        for station in stations_list:
            if station.type == 'TERMINAL':
                station.prod()

        # движение поездов
        for train in trains_list:
            if train.state == 'MOVING':
                shouldMove = True
                if train.route.stoppingPoints:
                    if train.lastStation == train.route.startingPoint:
                        for point in train.route.stoppingPoints:
                            if (train.distanceTravelled+train.speed > point.distance) & (train.distanceTravelled <= point.distance):
                                if not (point.openTime <= currentTime <= point.closeTime):
                                    if train.distanceTravelled != point.distance:
                                        train.distanceTravelled = point.distance
                                    shouldMove = False
                    else:
                        for point in reversed(train.route.stoppingPoints):
                            if (train.distanceTravelled + train.speed > train.route.distance - point.distance) & (
                                    train.distanceTravelled <= train.route.distance - point.distance):
                                if not (point.openTime <= currentTime <= point.closeTime):
                                    if train.distanceTravelled != train.route.distance - point.distance:
                                        train.distanceTravelled = train.route.distance - point.distance
                                    shouldMove = False
                if shouldMove:
                    train.move()


        print(f'{i} + -ый час')

        # погрузка/выгрузка на станциях
        for station in stations_list:
            if station.type == 'TERMINAL':
                station.putLoadTrainOnTrack()

            station.loadTrains()
            if station.type == 'TRANSSHIPMENT':
                station.putUnloadTrainOnTrack()
                station.unloadTrains()
                # moving_trains = []
                # for train in trains_list:
                #     if (train.state == 'MOVING') & (train.route.endingPoint == station):
                #         moving_trains.append((train, calculate_train_arrival_time(train, currentTime)))
                #
                # totalCap = station.curCap
                # unloadSpeed = 0
                # loadSpeed = 0
                # loadCap = station.accumCap
                #
                # for train in station.trainList:
                #     if train != 'Empty':
                #         if train.state == 'UNLOADING':
                #             totalCap += train.curCap
                #             unloadSpeed += station.unloadSpeed
                #         if train.state == 'LOADING':
                #             loadCap += station.accumCap - train.curCap
                #             loadSpeed += station.loadSpeed
                #
                # if moving_trains:
                #     moving_trains = sorted(moving_trains, key=lambda x: x[1])
                #     for train in moving_trains:
                #         arrival_time = (train[1] - startTime).total_seconds() / discreteness


            # запись в бд
            if station.name != 'Полярный':
                query = f"insert into {station.name} values (%s, %s, %s, %s, %s)"
                values = (startTime, station.curCap, station.lastProd,
                          station.trainList[0].name if station.trainList[0]!='Empty' else None,
                          station.trainList[0].curCap if station.trainList[0]!='Empty' else None)
                cursor.execute(query, values)
            else:
                query = f"insert into {station.name} values (%s, %s, %s, %s, %s, %s, %s, %s)"
                values = (startTime, station.curCap,
                          station.trainList[0].name if station.trainList[0] != 'Empty' else None,
                          station.trainList[0].curCap if station.trainList[0] != 'Empty' else None,
                          station.trainList[1].name if station.trainList[1]!='Empty' else None,
                          station.trainList[1].curCap if station.trainList[1]!='Empty' else None,
                          station.trainList[2].name if station.trainList[2]!='Empty' else None,
                          station.trainList[2].curCap if station.trainList[2]!='Empty' else None)
                cursor.execute(query, values)

            connection.commit()

            print(station.name)
            print('Текущее кол-во нефти: ', station.curCap)
            print('Поезда в ожидании:')
            for train in station.trainQueue:
                print(f'Название {train.name}, нефть: {train.curCap}, состояние: {train.state}')

            print('Поезда на путях:')
            for train in station.trainList:
                if train != 'Empty':
                    print(f'Название {train.name}, нефть: {train.curCap}, состояние: {train.state}')
                else:
                    print(train)

        print('Поезда в движении:')
        for train in trains_list:
            if train.state == 'MOVING':
                print(f'Название {train.name}, нефть: {train.curCap}, расстояние: {train.distanceTravelled}, состояние: {train.state}, маршрут: {train.route.name}')
        print()

    cursor.close()
    connection.close()
