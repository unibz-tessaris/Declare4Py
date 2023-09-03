import time
import csv
import pdb
import sys
import os
import pathlib
import json
SCRIPT_DIR = pathlib.Path("../", "src").resolve()
sys.path.append(os.path.dirname(SCRIPT_DIR))
from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.ConformanceChecking.LTLAnalyzer import LTLAnalyzer
from src.Declare4Py.ProcessModels.LTLModel import LTLTemplate, LTLModel

list_logs = ["teleclaims(2500traces)"] #"repair_example(500 traces)", "Sepsis(1000 traces)", "teleclaims(2500traces)", "Road_Traffic_Fine_Management_Process"]
list_filters = ["five_filters", "ten_filters", "twenty_filters", "fifteen_filters"]
list_filters = ["twenty_filters"]
folder_logs = "test_logs"
folder_jsons = "filters_jsons"
iterations = 2

if __name__ == "__main__":
    with open(os.path.join("test_performance", "performance_ltl_analyzer.csv"), 'a') as f:
        for log_name in list_logs:

            log_path = os.path.join(folder_logs, f"{log_name}.xes")
            event_log = D4PyEventLog(case_name="case:concept:name")
            event_log.parse_xes_log(log_path)

            for filter_name in list_filters:
                filter_path = os.path.join(folder_jsons, f"{filter_name}.json")
                json_file = open(filter_path)
                data = json.load(json_file)
                inst_model: LTLModel = None
                # For MP change "jobs" field in the jsons
                jobs = None
                templates: [str] = []
                for i, exp in enumerate(data):
                    print(exp)
                    jobs = exp["jobs"]
                    if exp["category"] == "LTL":
                        model_template = LTLTemplate(exp["filteringMode"])
                        param = exp["parameterValue"]
                        if i == 0:
                            inst_model = model_template.fill_template(param, attr_type=exp["attributeType"])
                        else:
                            func = model_template.templates.get(exp["filteringMode"])
                            templates.append(func(param, exp["attributeType"]))
                    else:
                        model_template = LTLTemplate(exp["filteringMode"])
                        source = exp["parameterValue"][0]
                        target = exp["parameterValue"][1]
                        if i == 0:
                            inst_model = model_template.fill_template(source, target, attr_type=exp["attributeType"])
                        else:
                            func = model_template.templates.get(exp["filteringMode"])
                            templates.append(func(source, target, attr_type=exp["attributeType"]))

                LTLTemplate.add_conjunction(inst_model, templates)
                inst_model.to_lydia_backend()
                analyzer = LTLAnalyzer(event_log, inst_model)
                times = []
                for j in range(iterations):
                    start = time.time()
                    df = analyzer.run(jobs=jobs, minimize_automaton=False)
                    end = time.time()
                    exec_time = end - start
                    print(exec_time)
                    times.append(exec_time)

                row = [log_name, filter_name, exp["category"], "AND_model", f"{jobs}_job"] + times + [inst_model.formula]
                writer = csv.writer(f)
                writer.writerow(row)
