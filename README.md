# PatientPaths

![PatientPaths CI](https://github.com/anu-act-health-covid19-support/patientpaths/workflows/PatientPaths%20CI/badge.svg)

> **NOTE**: `patientpaths` is currently (pre-alpha quality software). So if you've 
> got suggestions/feedback on the design---especially if you work in healthcare 
> and have a need for this sort of modelling---then please do get in touch, 
> but be wary that it's not yet ready for clinical use.

`patientpaths` is a Python toolkit for clinical pathway modelling.

**If** you have

1. data about the capacity of your health system (e.g. number of ward/ICU beds);
   and

2. one (or more) forecasts of the number of infections you're expecting in the
   population (e.g. the outputs from an infection model based on local data)

**then** `patientpaths` can be modified to simulate the flow of these patients through your
health system, e.g. _presentation at emergency department_ → _ward bed_ → _ICU
bed_ → _ward bed_ (recovery) → _discharge_.

## Features

- no proprietary software required (just Python v3.6+ with
  [NumPy](https://numpy.org))

- customisable for the specific capacities & pathways within your health
  system (see _Using `patientpaths`_ below)

- open source (GPLv3 licence)

## Setup

`pip install .` will install the `patientpaths` executable in your Python
environment, along with all the dependencies (`numpy`).

If you are using a linux or OSX computer which ships with a very old version
of Python, like the past-end-of-life Python 2, you may need to use `pip3` or
another distribution-specific install command.

## Using `patientpaths`

modify the code of the model_of_care.py file with the numerical parameters of your healthcare system, 
and adjust as needed the elements of your healthcare pathway and their interconnections via code in outcomes_for_moc.py file.
execute example_run.py for a quick demonstration run of the software.

the outcomes_for_moc.py file contains the bulk of the pathway description and is executed by calling the outcomes_for_moc function.
The outcomes_for_moc function takes 4 input parameters, a moc (model of care) string identifying a moc profile specified in model_of_care.py,
two arrays specifying mild and severe cases occuring per cohort per day, and a 'risk' array, identifying specific cohorts 'at risk'.

Specificially run a pathways simulation for presenting cases (mild and severe) in cohorts (S) across days a number of days (D), inputs are:
- moc: a string identifying the model of care profile name specified in model_of_care.py (presently either: 'default','cohort','clinics','phone')
- di_mild: a numpy array of dimension [S, D], identifying mild cases presenting to the clinical pathway of strata (S) per day (D)
- di_sev: a nunpy array of dimension [S, D], identifying severe cases presenting to the clinical pathway per day (must be of same dimension as di_mild)
- risk: a one dimensional numpy array [S], which is a number for each cohort, which if greater than one identifies the cohort as being 'at risk' with slightly different dynamics.

Outputs from the simulation include a range of different arrays identifying different factors per day of the simulation, including:
 * deaths: number of deaths from each of the cohorts across days of the simulation
 * excess_{icu,ward,ed_sev,ed_mld,clinic_mld,clinic_sev,gp}: the vectors of numbers not admitted to each of the services on a given day
 * admit_{icu,ward,ed_sev,ed_mld,clinic_mld,clinic_sev,gp}: the vectors of numbers admitted to each of the services on a given day
 * avail_{ed,clinic,gp,icu,ward}: the numbers of unused capacity of each of the resources on a given day

The resources are:
 * The ICU - intensive care unit, only available to severe cases, excess patients directly results in deaths
 * The Wards and Emergency Departments, share beds between them and can accommodate severe and mild cases
 * the Specialty Clinical pathway specifically for treatments
 * and General Practitioners, specifically for treating mild cases

The specific pathway described by the code is a reimplementation of MATLAB code developed for modelling Australian Covid spread, originally modified from the pathway described by paper:
> Robert Moss, James M. McCaw, Allen C. Cheng, Aeron C. Hurt, and Jodie McVernon. "Reducing disease burden in an influenza pandemic by targeted delivery of neuraminidase inhibitors: mathematical models in the Australian context." BMC Infectious Diseases, 16(1):552, October 2016. ISSN 1471-2334, doi:10.1186/s12879-016-1866-7.


## Licence

See `LICENCE`.
