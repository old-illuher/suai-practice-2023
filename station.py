import random
import copy
import model

class Station:
    name: str
    type: str
    loadSpeed: float  # скорость погрузки
    curCap: float  # текущее кол-во нефти
    wayNum: int  # количество путей для погрузки/выгрузки
    trainQueue: list  # очередь составов, ожидающих освобождение пути
    trainList: list  # составы, находящиеся на путях погрузки/выгрузки

    def __init__(self, data):
        self.name = data['name']
        self.type = data['type']
        self.loadSpeed = data['loadSpeed']
        self.curCap = data['curCap']
        self.wayNum = data['wayNum']
        self.trainQueue = []
        self.trainList = ['Empty']*self.wayNum


    def loadTrains(self):
        for train in self.trainList:
            if train == 'Empty':
                continue

            if train.state == 'WAITING':
                train.state = 'LOADING'
                continue

            if self.loadSpeed > train.maxCap - train.curCap:
                loadValue = train.maxCap - train.curCap
            else:
                loadValue = self.loadSpeed
            if self.curCap >= loadValue:
                train.load(loadValue)
                self.curCap -= loadValue
            else:
                train.load(self.curCap)
                self.curCap = 0

            if train.curCap == train.maxCap:
                index = self.trainList.index(train)
                self.trainList[index] = 'Empty'
                train.state = 'MOVING'


class Terminal(Station):
    prodSpeed: tuple    # добыча в формате (среднее значение, СКО)
    lastProd: float

    def __init__(self, data):
        super().__init__(data)
        self.prodSpeed = (data['prodSpeed']['mean'], data['prodSpeed']['SD'])

    def prod(self):
        self.lastProd = random.normalvariate(self.prodSpeed[0], self.prodSpeed[1]).__int__()
        self.curCap += self.lastProd

    def putLoadTrainOnTrack(self):
        if 'Empty' in self.trainList:
            index = self.trainList.index('Empty')
            # fifo
            for train in self.trainQueue:
                if train.maxCap <= self.curCap:
                    self.trainQueue.remove(train)
                    # train.state = 'LOADING'
                    self.trainList[index] = train
                    return train
                else:
                    diff = train.maxCap - self.curCap
                    if (self.curCap/self.loadSpeed)*self.prodSpeed[0] < diff:
                        break
                    else:
                        self.trainQueue.remove(train)
                        self.trainList[index] = train
                        return train
            return False
        else:
            return False


class TransshipmentPoint(Station):
    unloadSpeed: float  # скорость выгрузки
    maxCap: float       # макимальная емкость
    accumCap: float     # объем, при котором происходит отгрузка
    transshipmentTrains: list

    def __init__(self, data):
        super().__init__(data)
        self.unloadSpeed = data['unloadSpeed']
        self.maxCap = data['maxCap']
        self.accumCap = data['accumCap']
        self.transshipmentTrains = []

    def putUnloadTrainOnTrack(self):
        if 'Empty' in self.trainList:
            index = self.trainList.index('Empty')
            trainsCap = 0

            # подсчет суммарного кол-ва нефти с учетом составов на путях
            for train in self.trainList:
                if train != 'Empty':
                    if (train.state == 'UNLOADING') | (train.state == 'WAITING'):
                        trainsCap += train.curCap


            for train in self.trainQueue:
                if train.curCap + self.curCap + trainsCap > self.maxCap:
                    continue
                else:
                    self.trainQueue.remove(train)
                    # train.state = 'UNLOADING'
                    self.trainList[index] = train
                    return train
        else:
            return False

    def putLoadTrainOnTrack(self):
        if 'Empty' in self.trainList:
            index = self.trainList.index('Empty')
            train = copy.deepcopy(self.transshipmentTrains[0])
            train.state = 'LOADING'
            self.trainList[index] = train

    def loadTrains(self):
        for train in self.trainList:
            if train == 'Empty':
                continue

            if train.state == 'LOADING':
                if self.loadSpeed > train.maxCap - train.curCap:
                    loadValue = train.maxCap - train.curCap
                else:
                    loadValue = self.loadSpeed
                if self.curCap >= loadValue:
                    train.load(loadValue)
                    self.curCap -= loadValue
                else:
                    train.load(self.curCap)
                    self.curCap = 0

                if train.curCap == train.maxCap:
                    train.state = 'MOVING'
                    index = self.trainList.index(train)
                    self.trainList[index] = 'Empty'

    def unloadTrains(self):
        for train in self.trainList:
            if train == 'Empty':
                continue

            if train.state == 'WAITING':
                train.state = 'UNLOADING'
                continue

            if train.state == 'UNLOADING':
                if train.curCap >= self.unloadSpeed:
                    train.unload(self.unloadSpeed)
                    self.curCap += self.unloadSpeed
                else:
                    self.curCap += train.curCap
                    train.unload(train.curCap)
                    train.state = 'MOVING'
                    index = self.trainList.index(train)
                    self.trainList[index] = 'Empty'
        # учитывать подъезжающие составы
        totalCap = self.curCap
        loadCap = self.accumCap

        for train in self.trainList:
            if train != 'Empty':
                if train.state == 'UNLOADING':
                    totalCap += train.curCap
                if train.state == 'LOADING':
                    loadCap += self.accumCap - train.curCap

        if totalCap >= loadCap:
            self.putLoadTrainOnTrack()
