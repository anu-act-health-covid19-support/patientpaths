class Presentation_Matrix:
    values = None
    multipliers = None
    default = None

    def __init__(self):
        self.values = {}
        self.multipliers = {}

    def set_default(self, default):
        self.default = default

    def transition(self, from_label, to_label, multiplier):
        if from_label not in self.multipliers.keys():
            self.multipliers[from_label] = {}
        self.multipliers[from_label][to_label] = multiplier
        self[from_label] = self[from_label]
        self[to_label] = self[to_label]

    def __setitem__(self, label, value):
        self.values[label] = value

    def __getitem__(self, label):
        return self.values.get(label, self.default)

    def apply(self):
        old_values = self.values.copy()
        for key in self.values.keys():
            self.values[key] = self.default
        for from_label in self.multipliers.keys():
            for to_label in self.multipliers[from_label].keys():
                if from_label not in old_values.keys():
                    raise Exception("presentation matrix trying to access unset data")
                self.values[to_label] += (
                    self.multipliers[from_label][to_label] * old_values[from_label]
                )
