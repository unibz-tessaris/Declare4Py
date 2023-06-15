# Declare4Py

Declare4Py is the first Python package for declarative Process Mining with core functionalities to 
easily implement Machine Learning applications for Process Mining. Declarative process mining uses 
declarative behavioural rules (based on Linear Temporal Logic on finite traces) for defining process models. This 
results in a high flexibility of the business process model definition without neglecting hard 
constraints that must be satisfied. Moreover, declarative languages can be used as a bridge between 
Process Mining and Machine learning with the DECLARE encoding that encodes the traces in a log into a 
numeric format suitable as input to Machine Learning algorithms. Declare4Py implements such a bridge 
by including standard algorithms for:

1. declarative Process Mining with LTLf or (MP)-DECLARE templates (e.g., conformance checking, model discovery, trace generation, query checking);
2. log encodings (e.g., complex-index, aggregate, Declare);
3. log labelling according to filtering or declarative rules.

All the Declare4Py data formats are compatible with the main Machine Learning Python packages: scikit-learn, Tensorflow and PyTorch.


## Installation
We suggest to use a virtual environment in order to avoid the clashes between python version and the required libraries.

- From project root run `python -m venv venv`
- activate the virtual environment `source venv/Scripts/activate`
- install libraries
- `python -m pip install .` to install the dependencies of the project, it will read the pyproject.toml


## Tutorials
The `docs/source/tutorials/` folder contains a walk-through of Declare4Py. In order, the tutorials cover the following topics:

1. [Managing event logs](https://github.com/francxx96/declare4py/blob/main/tutorials/system_overview.ipynb): methods to manage event logs, importing them, extracting useful information, converting them in other formats;
2. [Managing process models](https://github.com/ivanDonadello/declare4py-v2.0/blob/v1.0.1/refactor-architecture/tutorials/Log_information.ipynb): simple methods to parse and manage process models from strings and/or files and checking their satisfiability;
3. [Conformance checking of LTLf templates/formulas](https://github.com/francxx96/declare4py/blob/main/tutorials/conformance_checking.ipynb): check what are the traces in an event log that satisfy a given LTLf model;
4. [Conformance checking of MP-DECLARE templates](https://github.com/francxx96/declare4py/blob/main/tutorials/model_discovery.ipynb): check what are the traces in an event log (along with the fulfillments/violations) that satisfy a given MP_DECLARE model;
5. [Query Checking with DECLARE models](https://github.com/francxx96/declare4py/blob/main/tutorials/query_checking.ipynb): discover what are the activities that make an input DECLARE constraint satisfied in an event log.
6. [Discovery of DECLARE models](): discover what are the most satisfied DECLARE constraints in an event log;
7. [Filtering an event log](): select a subset of an event log that satisfy some input properties.

The tutorials are Jupyter notebooks and consider the [Sepsis cases log](https://data.4tu.nl/articles/dataset/Sepsis_Cases_-_Event_Log/12707639).

## Repository Structure
- `src/declare4py/ProcessModels` -- the implementation of the supported process models.
- `src/declare4py/ProcessMiningTasks/` -- the implementation of the supported Process Mining tasks.
- `tests/` -- a collection of tests for computing the Declare4Py performance.
- `docs/source/tutorials/` -- tutorials to start with Declare4Py,

## Citing Declare4Py
If you use Declare4Py in your research, please use the following BibTeX entry.

```
@inproceedings{DonadelloRMS22,
  author    = {Ivan Donadello and
               Francesco Riva and
               Fabrizio Maria Maggi and
               Aladdin Shikhizada},
  title     = {Declare4Py: {A} Python Library for Declarative Process Mining},
  booktitle = {{BPM} (PhD/Demos)},
  series    = {{CEUR} Workshop Proceedings},
  volume    = {3216},
  pages     = {117--121},
  publisher = {CEUR-WS.org},
  year      = {2022}
}
```
