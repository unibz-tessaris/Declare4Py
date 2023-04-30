
from __future__ import annotations

import cProfile
import logging

from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.asp_generator import AspGenerator
from src.Declare4Py.ProcessModels.DeclareModel import DeclareModel
import time
from datetime import datetime
import json

# profiler = cProfile.Profile()
# profiler.enable()
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/declare_models/BusinessTrip.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/declare_models/xRay.decl")
    model: DeclareModel = DeclareModel().parse_from_file("../../tests/declare_models/drive_test.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model1.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model2.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model2.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model4.decl")
    print("Total Activities/Events: ", model.parsed_model.get_total_events())
    print("Total Attributes: ", len(model.parsed_model.attributes_list))
    print("Total Constraints: ", len(model.parsed_model.templates))

    num_of_traces = 5
    num_min_events = 5
    num_max_events = 10

    asp = AspGenerator(model, num_of_traces, num_min_events, num_max_events)
    asp.run_parallel_fn(output_file="../../output/generated.parallel.xes")


