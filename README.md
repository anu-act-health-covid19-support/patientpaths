# PatientPaths

![PatientPaths CI](https://github.com/anu-act-health-covid19-support/patientpaths/workflows/PatientPaths%20CI/badge.svg)

> **NOTE**: `patientpaths` is currently under active development (pre-alpha
> quality software). So if you've got suggestions/feedback on the
> design---especially if you work in healthcare and have a need for this sort of
> modelling---then please do get in touch, but be wary that it's not yet ready
> for clinical use.

`patientpaths` is an open and accessible Python toolkit for clinical pathway
modelling.

**If** you have

1. data about the capacity of your health system (e.g. number of ward/ICU beds);
   and

2. one (or more) forecasts of the number of infections you're expecting in the
   population (e.g. the outputs from an infection model based on local data)

**then** `patientpaths` can simulate the flow of these patients through your
health system, e.g. _presentation at emergency department_ → _ward bed_ → _ICU
bed_ → _ward bed_ (recovery) → _discharge_.

## Features

- no proprietary software required (just Python v3.6+ with
  [NumPy](https://numpy.org))

- modular (consumes input data & provides output results in
  [JSON](https://www.json.org/json-en.html) format for easy integration with
  other tools)

- highly customisable for the specific capacities & pathways within your health
  system (see _Using `patientpaths`_ below)

- open source (GPLv3 licence)

## Setup

`pip install .` will install the `patientpaths` executable in your Python
environment, along with all the dependencies (`numpy`).

If you are using a linux or OSX computer which ships with a very old version
of Python, like the past-end-of-life Python 2, you may need to use `pip3` or
another distribution-specific install command.

## Using `patientpaths`

TODO

## Licence

See `LICENCE`.
