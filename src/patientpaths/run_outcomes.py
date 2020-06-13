import click
from .Directive_Matrix import Directive_Matrix
import json
import numpy as np
import networkx as nx
from .components import PatientPathsComponent
from .utils import enumerate_all_sublists
from networkx.algorithms.dag import topological_sort


def run_outcomes(config):
    components = {
        component.__name__: component
        for component in PatientPathsComponent.__subclasses__()
    }
    G = nx.DiGraph()
    pole_names = []
    for p in config["poles"]:
        pole_names.append(p["name"])
    matrix = Directive_Matrix(pole_names)
    for p in config["poles"]:
        if isinstance(p["initial_value"], list):
            matrix.values[p["name"]] = np.array(p["initial_value"])
        else:
            matrix.values[p["name"]] = p["initial_value"]
    matrix.apply()
    for i, c in enumerate(config["components"]):
        G.add_node(i)
        for input_key in components[c["kind"]].inputs:
            assert input_key in c["parameters"].keys()
            for node_input in enumerate_all_sublists(c["parameters"][input_key]):
                if isinstance(node_input, str):
                    if node_input not in pole_names:
                        G.add_edge(node_input, i)
        for output_key in components[c["kind"]].outputs:
            assert output_key in c["parameters"].keys()
            for node_output in enumerate_all_sublists(c["parameters"][output_key]):
                if isinstance(node_output, str):
                    if node_output not in pole_names:
                        G.add_edge(i, node_output)
    assert (
        len(list(nx.simple_cycles(G))) == 0
    ), "component graph contains a cycle {}".format(list(nx.simple_cycles(G)))
    sorted_topology = [l for l in topological_sort(G) if isinstance(l, int)]
    for i in sorted_topology:
        matrix.add_component(**(config["components"][i]))
    data = []
    for day in range(config["num_days"]):
        matrix.apply()
        data.append(matrix.values.values.copy())
    return data


@click.command()
@click.argument("filename", type=click.Path(exists=True))
def file_outcomes(filename):
    with open(filename, "r") as f:
        config = json.load(f)
    config_keys = list(config.keys())
    assert "components" in config_keys, "config needs component specification"
    assert "poles" in config_keys, "config needs poles specification"
    assert "num_days" in config_keys, "config needs num_days specified"
    config_keys.remove("components")
    config_keys.remove("poles")
    config_keys.remove("num_days")
    config_keys = sorted(config_keys)[::-1]
    print("running experiment:")
    for k in config_keys:
        print("{}\t{}".format(k, config[k]))
    print("")
    for c in run_outcomes(config):
        print(c)


if __name__ == "__main__":
    file_outcomes()
