
import logging
import time

from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.asp_generator import AspGenerator
from src.Declare4Py.ProcessModels.DeclareModel import DeclareModel
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/declare_models/BusinessTrip.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/declare_models/xRay.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/declare_models/drive_test.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model1.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model2.decl")
    model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model3.decl")
    # model: DeclareModel = DeclareModel().parse_from_file("../../tests/test_models/model4.decl")
    print("Total Activities/Events: ", model.parsed_model.get_total_events())
    print("Total Attributes: ", len(model.parsed_model.attributes_list))
    print("Total Constraints: ", len(model.parsed_model.templates))

    num_of_traces = 10
    num_min_events = 40
    num_max_events = 62

    start = time.time()
    asp = AspGenerator(model, num_of_traces, num_min_events, num_max_events)
    # asp.set_custom_trace_lengths({
    #     40: 10,
    #     42: 7,
    #     47: 8,
    #     46: 4,
    #     57: 5,
    #     55: 5,
    #     51: 4,
    #     60: 3,
    #     62: 4,
    #     # 40: 10, 42: 1, 47: 1, 46: 1, 57: 2, 60: 10, 62: 20, 55: 5, 51: 10
    # })

    asp.run_parallel_fn(output_file="..\..\output\generated.xes", workers=5)
    asp.wait_process()


    # asp.run('../../output/generated_asp.lp')
    # asp.to_xes("../../output/generated23.xes")
    print("Ends", time.time() - start)

