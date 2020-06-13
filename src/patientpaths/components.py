import numpy as np


class PatientPathsComponent(object):
    inputs = []
    outputs = []

    def apply(self, values, static):
        raise Exception("Component unimplemented error - apply function")

    def finalise(self, values, static):
        raise Exception("Component unimplemented error - finalise function")


class allocate(PatientPathsComponent):
    inputs = ["_demand"]
    outputs = ["_admit", "_excess"]

    def __init__(self, length_of_stay, capacity, _demand, _admit, _excess, buffer_name):
        self.length_of_stay = length_of_stay
        self.capacity = capacity
        self.buffer_name = buffer_name
        self._demand = _demand
        self._admit = _admit
        self._excess = _excess

    def apply(self, values, static):
        if self.buffer_name not in static.keys():
            static[self.buffer_name] = []
        while (len(static[self.buffer_name]) > 0) and (static[self.buffer_name][0] < 0):
            static[self.buffer_name] = static[self.buffer_name][1:]
        admit = values[self._demand] * 0
        excess = values[self._demand] * 0
        if len(static[self.buffer_name]) > 0:
            capacity = self.capacity - static[self.buffer_name][0]
        else:
            capacity = self.capacity
        for s in range(len(values[self._demand])):
            admit_value = min(capacity, float(values[self._demand][s]))
            admit[s] = admit_value
            excess[s] = values[self._demand][s] - admit_value
            capacity = capacity - admit_value
            if admit_value > 0:
                for i in range(self.length_of_stay):
                    if len(static[self.buffer_name]) <= i:
                        static[self.buffer_name].append(admit_value)
                    else:
                        static[self.buffer_name][i] += admit_value
        values[self._admit] = admit
        values[self._excess] = excess

    def finalise(self, values, static):
        if len(static[self.buffer_name]) > 0:
            static[self.buffer_name][0] = -1


class sum_vector(PatientPathsComponent):
    inputs = ["_from"]
    outputs = ["_to"]

    def __init__(self, _to, _from):
        self._to = _to
        self._from = _from

    def apply(self, values, static):
        values[self._to] = np.sum(values[self._from])

    def finalise(self, values, static):
        pass


class transfer(PatientPathsComponent):
    inputs = ["_from"]
    outputs = ["_to"]

    def __init__(self, _to, _from):
        self._to = _to
        self._from = _from

    def apply(self, values, static):
        s = 0
        for f in self._from:
            m = 1
            for v in f:
                if isinstance(v, str):
                    m *= values[v]
                else:
                    m *= v
            s += m
        values[self._to] = s

    def finalise(self, values, static):
        pass


class queue(PatientPathsComponent):
    inputs = ["_from"]
    outputs = ["_to", "_queued"]

    def __init__(self, _to, _from, _queued, size):
        self._to = _to
        self._from = _from
        self._queued = _queued
        self.size = size
        self.buffer = [None for i in range(size)]

    def apply(self, values, static):
        if self.buffer[-1] is None:
            values[self._to] = values[self._from] * 0
        else:
            values[self._to] = self.buffer[-1]
        for i in range(len(self.buffer) - 1, 0, -1):
            self.buffer[i] = self.buffer[i - 1]
        self.buffer[0] = values[self._from]
        values[self._queued] = np.sum([b for b in self.buffer if b is not None])

    def finalise(self, values, static):
        pass
