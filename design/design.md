---
title: patientpaths design sketch
author: Ben Swift & contributors
bibliography: references.bib
link-citations: true
reference-section-title: References
---

This is a place to sketch out a design for patientpaths to make it maximally
useful for all the relevant folks. It's not a UML diagram, it's a document for
humans, although it might get into the implementation details as well. If you've
got questions/suggestions or would like to get in touch, contact
[Ben](mailto:ben.swift@anu.edu.au).

# Prior art

## Academic literature

[@aspland2019clinical] is the most up-to-date (academic) survey on what's out
there in terms of clinical pathway modelling. Most of the projects described
don't actually release the software, but a few do, and we should track them
down.

## Software tools

### Stocks & Flows

If we consider this as a more general "stocks and flows" problem, there are
_lots_ of related software tools for doing this sort of thing. One early
challenge for this project will be figuring out whether it's worth glomming onto
one of these existing tools, or starting from scratch.

TODO make a list of such tools.

### Epidemiological models

TODO we should also make a note of other models (e.g. infection models). This
will be important for making sure that our tool plays nice with the rest of the
ecosystem (such as it is).

# Users

## Software devs

These are potential contributors, in source code, tests, documentation,
translations/localisations, etc.

## Health system admins

These are folks who work in health systems, potentially making decisions about
allocations of resources.

## Health system workers

TODO not sure if this is a separate user group form the admins?

## Politicians

These are decisionmakers without specific health system expertise, but who
potentially have oversight into resourcing decisions within the health system.

# People

_because "users" is a bit gauche, and stakeholders is too MBAish_

There are several different groups of people to keep in mind when designing patientpaths:

- **Epidemiologists** are the people who design the models for simulating the
  spread & impact of disease through the population. They ensure that what the
  model/simulation _says_ will happen as people get sick, spread the disease,
  and are cared for by the health system best reflects what will _actually_
  happen.

- **Hospital administrators** are responsible for configuring patientpaths so
  that it knows the specific capacities and pathways within their specific
  health system (because all health systems are different), modelling
  _different_ configurations of the health system (to see how things might be
  done differently).

- **Domain-expert policymakers** are people within the health system (i.e.
  domain experts) who need to make decisions about resource allocation.

- **Non-domain-expert policymakers** are people outside (or "above") the health
  system who don't necessarily have the specific domain expertise, but who are
  in charge of making decisions about how resources will be allocated (e.g.
  politicians).

- **Software engineers** are people who take the models from the epidemiologists
  and write the software so that they will run reliably and efficiently.

- **UX designers** are people who make sure that the experience of actually
  using patientpaths (providing inputs, consuming outputs) is a good one.

- **Technical writers** are necessary to make sure that the documentation and
  scaffolding for this project serves all the above groups and makes it easy for
  them to do their job and make the most of what patientpaths can do for them.

# Data

## Inputs

There are two types of inputs to patientpaths:

- **Health system topology** inputs are descriptions of the type, capacity and
  pathways through the different resources in the health system. These might be
  detailed, and will take some time to collate for a specific health system
  context, but probably won't change often. Within this topology, there are two
  different types of inputs:
  - _capacities_, e.g. the number of ICU beds, the number of PPE masks (these
    are the "stocks", or at least they place upper bounds on the stocks)
  - _pathways_, e.g. what happens to patients when they get sick? what happens if
    they get worse? what's the back-up plan if the care resource they need isn't
    available? (these are the "flows")

- **Infection model** inputs are time series (either real or simulated) of
  presentations of sick people---these are the "inputs" to the health system.
  These type of inputs (especially in the modelling case) are easy to produce,
  and lots of different scenarios can be modelled (perhaps extracting summary
  statistics). These inputs will have a daily resolution, and may include
  "strata" information (i.e. have the daily presentations broken down by
  different population strata)

## Outputs

- **Summary statistics** like deaths, capacity limits, etc.

- **Visualisations** of some of the most important metrics.

- **Full utilisation data** (i.e. a timeseries of the utilisation of each
  resource on each day) might be handy in some circumstances; especially as
  inputs to other modelling tools.

# Interface notes

There are two main interfaces:

1. the "tell patientpaths what my health system looks like" interface

2. the "what will happen in my health system under this particular disease
   scenario" interface

Interface #2 is not dissimilar to what we built for the ACT-ANU taskforce MVP;
it's interface #1 which is completely new (and in some ways is the more
challenging part of the project, interface-wise).

# Software notes

Our priorities are:

- no proprietary tools

- no need for complicated statistical/stochastic elements in the "core" model;
  sampling & estimating distributions can happen one level up the abstraction
  tree[^stochastic]

- prefer plain text (inc. csv) to bespoke data formats, because the systems this
  will interact with will probably require those formats for data interchange
  anyway
  
[^stochastic]:
    there are pros & cons to this; the other option is to go full bayesian
    (which I'm not closed to) but it's probably better to do one or the other
