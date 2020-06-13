from .components import PatientPathsComponent


class ValueList:
    values = None
    update_values = None
    poles = None

    def __init__(self, poles):
        self.values = {}
        self.update_values = {}
        self.poles = poles

    def __setitem__(self, label, value):
        if label in self.poles:
            if label not in self.update_values.keys():
                self.update_values[label] = value
            else:
                self.update_values[label] += value
        else:
            self.values[label] = value

    def __getitem__(self, label):
        if label not in self.values.keys():
            raise Exception(
                "ERROR: drawing apon a value {} that is not initialised".format(label)
            )
        return self.values[label]

    def apply(self):
        for k in self.update_values.keys():
            self.values[k] = self.update_values[k]
        self.update_values.clear()


class Directive_Matrix:
    component_classes = None
    components = None
    values = None
    static_dict = None

    def __init__(self, poles):
        self.component_classes = {
            component.__name__: component
            for component in PatientPathsComponent.__subclasses__()
        }
        self.components = []
        self.values = ValueList(poles)
        self.static_dict = {}

    def add_component(self, kind, parameters):
        self.components.append(self.component_classes[kind](**parameters))

    def apply(self):
        for c in self.components:
            c.apply(self.values, self.static_dict)
        self.values.apply()
        for c in self.components:
            c.finalise(self.values, self.static_dict)
