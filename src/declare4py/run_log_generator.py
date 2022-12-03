
from boolean import boolean
import logging
from future import annotations
from src.declare4py.log_utils.log_analyzer import LogAnalyzer
from src.declare4py.log_utils.parsers.declare.declare_parsers import DeclareParser
from src.declare4py.models.log_generation.asp.asp_generator import AspGenerator

logging.basicConfig(level=logging.INFO)

decl = """
activity Driving_Test
bind Driving_Test: Driver, Grade
activity Getting_License
bind Getting_License: Driver
activity Resit
bind Resit: Driver, Grade
activity Test_Failed
bind Test_Failed: Driver
Driver: Fabrizio, Mike, Marlon, Raimundas
Grade: integer between 1 and 5
# Response[Driving_Test, Getting_License] |A.Grade>2 | |
Response[Driving_Test, Getting_License] | |T.Grade>2 |
Response[Driving_Test, Resit] |A.Grade<=2 | |
Response[Driving_Test, Test_Failed] |A.Grade<=2 | |
"""


dp = DeclareParser()
model = dp.parse_from_string(decl)
# print(d.parsed_model)
num_of_traces = 4
num_min_events = 2
num_max_events = 4
asp = AspGenerator(
    model, num_of_traces, num_min_events,
    num_max_events, distributor_type="gaussian",
    loc=3, scale=0.8
)

asp.run()
# asp.to_xes("../../generated_xes.xes")


# TODO: ask how to implement TIME CONDITION in asp
# TODO: Ask Chiarello whether the generated output of lp is correct


