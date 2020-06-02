# PatientPaths

`patientpaths` is an open and accessible Python toolkit for clinical pathway
modelling. **If** you have

1. data about the capacity of your health system (e.g. number of ward/ICU beds);
   and

2. one (or more) forecasts of the number of infections you're expecting in the
   population (e.g. the outputs from an infection model based on local data)

**then** `patientpaths` can simulate the flow of these patients through your
health system, e.g. _presentation at emergency department_ → _ward bed_ → _ICU
bed_ → _ward bed_ (recovery) → _discharge_.

## Features

- no proprietary software required (just Python 3 with
  [NumPy](https://numpy.org))

- modular (consumes input data & provides output results in
  [JSON](https://www.json.org/json-en.html) format for easy integration with
  other tools)

- highly customisable for the specific capacities & pathways within your health
  system (see _Using `patientpaths`_ below)

- open source (GPLv3 licence)

## Setup

TODO

## Using `patientpaths`

TODO

## Licence

See `LICENCE`.
