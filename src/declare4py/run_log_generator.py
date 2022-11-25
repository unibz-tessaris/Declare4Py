try:
    from future import annotations
except:
    pass
from src.declare4py.log_utils.log_analyzer import LogAnalyzer
from src.declare4py.log_utils.parsers.declare.declare_parsers import DeclareParser
from src.declare4py.models.log_generation.asp.asp_generator import AspGenerator


decl = """activity A
bind A: grade
activity B
bind B: grade
grade: integer between 1 and 5
Response[A, B] |A.grade = 3 |T.grade = 5 |1,5,s
activity C
bind C: grade
grade: integer between 1 and 5
Response[A, B] |A.grade = 3 |T.grade > 5 |1,5,s"""

dp = DeclareParser()
d = dp.parse_from_string(decl)
# print(d.parsed_model)
num_of_traces = 4
num_min_events = 2
num_max_events = 4
log_analyzer = LogAnalyzer()
asp = AspGenerator(
    num_of_traces,
    num_min_events,
    num_max_events,
    d,
    # "tests/files/declare/Response2.decl",
    # "tests/files/lp/templates.lp",
    # "tests/files/lp/generation_encoding.lp",
    log_analyzer,
)

asp.run()
asp.to_xes("../../generated_xes.xes")


# TODO: ask how to implement TIME CONDITION in asp
# TODO: Ask Chiarello whether the generated output of lp is correct


