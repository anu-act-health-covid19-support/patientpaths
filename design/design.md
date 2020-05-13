---
title: patientpaths design sketch
author: Ben Swift & contributors
bibliography: references.bib
link-citations: true
reference-section-title: References
---

This is a place to sketch out a design for patientpaths to make it maximally
useful for all the relevant folks. It's not a UML diagram, it's a document for
humans, although it might get into the implementation details as well.

If you've got questions/suggestions or would like to get in touch, contact
[Ben](mailto:ben.swift@anu.edu.au).

## Prior art

[@aspland2019clinical] is the most up-to-date (academic) survey on what's out
there in terms of clinical pathway modelling. Most of the projects described
don't actually release the software, but a few do, and we should track them
down.

If we consider this as a more general "stocks and flows" problem, there are
_lots_ of related software tools for doing this sort of thing. One early
challenge for this project will be figuring out whether it's worth glomming onto
one of these existing tools, or starting from scratch.

TODO make a list of such tools.

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

# Data

## Inputs

There are two types of inputs to patientpaths:

- **Health system topology** inputs are descriptions of the type, capacity and
  pathways through the different resources in the health system. These might be
  detailed, and will take some time to collate for a specific health system
  context, but probably won't change often.

- **Infection model** inputs are time series (either real or simulated) of
  presentations of sick people---these are the "inputs" to the health system.
  These type of inputs (especially in the modelling case) are easy to produce,
  and lots of different scenarios can be modelled (perhaps extracting summary
  statistics). These inputs will have a daily resolution, and may include
  "strata" information (i.e. have the daily presentations broken down by
  different population strata)

## Outputs
