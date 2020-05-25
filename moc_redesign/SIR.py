import numpy as np
import xsimlab as xs

R0 = 1.1
recovery = 0.1

Recover = None  # hmm... circular foreign variables not allowed???


@xs.process
class Infect:
    S = xs.variable(intent="in")
    I = xs.variable(intent="out")
    new_R = xs.foreign(Recover, "new_R", intent="in")

    def run_step(self):
        self._I = self.I - self.new_R

    def finalize_step(self):
        self.S = self.S - R0 * self._I
        self.I = self._I + R0 * self._I


@xs.process
class Recover:
    I = xs.foreign(Infect, "I", intent="in")
    R = xs.variable(intent="out")
    new_R = xs.variable(intent="out")

    def run_step(self):
        self._I = self.I

    def finalize_step(self):
        self.new_R = recovery * self._I
        self.R = self.R + recovery * self._I


model = xs.Model({"Infect": Infect, "Recover": Recover})

input_dataset = xs.create_setup(
    model=model,
    clocks={"step": np.arange(9)},
    input_vars={"Infect__S": 1, "Infect__I": 0.1, "Recover__R": 0},
    output_vars={"Infect__S": "step"},
)

output_dataset = input_dataset.xsimlab.run(model=model)
