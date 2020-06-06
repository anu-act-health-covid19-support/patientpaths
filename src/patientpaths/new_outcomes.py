# OUTCOMES_FOR_MOC
import click
from Directive_Matrix import Directive_Matrix
import json


def run_outcomes(config):
    matrix = Directive_Matrix()
    for stage, components in enumerate(config["components"]):
        for c in components:
            matrix.add_component(c["type"], stage, c["parameters"])
    data = []
    for day in range(config["num_days"]):
        matrix.apply()
        data.append(matrix.values.values.copy())
    return data


@click.command()
@click.argument("filename", type=click.Path(exists=True))
def new_outcomes(filename):
    with open(filename, "r") as f:
        config = json.load(f)
    for c in run_outcomes(config):
        print(c)


if __name__ == "__main__":
    new_outcomes()
