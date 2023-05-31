.. Declare4py documentation master file, created by
   sphinx-quickstart on Mon Feb 13 16:13:03 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Declare4Py: a Python package for declarative Process Mining and Machine Learning
======================================
Declare4Py is the first Python package for declarative Process Mining with core functionalities to easily implement Machine Learning applications for Process Mining. Declarative process mining uses declarative behavioural rules (based on Linear Temporal Logic) for defining process models. This results in a high flexibility of the business process model definition without neglecting hard constraints that must be satisfied. Moreover, declarative languages can be used as a bridge between Process Mining and Machine learning with the DECLARE encoding that encodes the traces in a log into a numeric format suitable as input to Machine Learning algorithms. Declare4Py implements such a bridge by including standard algorithms for

1. declarative Process Mining (e.g., conformance checking, model discovery, trace generation, query checking);
2. log encodings (e.g., complex-index, aggregate, \Declare);
3. log labelling according to filtering or declarative rules.

All the Declare4Py data formats are compatible with the main Machine Learning Python packages: scikit-learn, Tensorflow and PyTorch.


.. toctree::
   :maxdepth: 2
   :hidden:
   
   installation.rst
   gettingstarted.rst
   documentation.rst
   tutorials.rst
   Publications.rst
   Credits.rst
   How to contribute.rst
   Citing.rst
