import time
import csv
import pdb
import sys
import os
import pathlib
import json

import numpy as np

SCRIPT_DIR = pathlib.Path("../", "src").resolve()
sys.path.append(os.path.dirname(SCRIPT_DIR))
from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.ConformanceChecking.LTLAnalyzer import LTLAnalyzer
from src.Declare4Py.ProcessModels.LTLModel import LTLTemplate, LTLModel

list_logs = ["repair_example(500 traces)", "Sepsis(1000 traces)", "teleclaims(2500traces)", "Road_Traffic_Fine_Management_Process"]
list_filters = ["5-filters", "10-filters", "15-filters", "20-filters"]
#list_filters = ["20-filters"]
folder_logs = "test_logs"
folder_jsons = "filters_jsons/LTLf"
iterations = 5

if __name__ == "__main__":
    with open(os.path.join("test_performance", "performance_ltl_analyzer.csv"), 'a') as f:
        for log_name in list_logs:

            log_path = os.path.join(folder_logs, f"{log_name}.xes")

            event_log = D4PyEventLog(case_name="case:concept:name")
            event_log.parse_xes_log(log_path)

            for filter_name in list_filters:
                print(f"Processing {log_name.upper()} with {filter_name.upper()} ...")
                filter_path = os.path.join(folder_jsons, log_name, f"{filter_name}.json")
                json_file = open(filter_path)
                data = json.load(json_file)
                # For MP change "jobs" field in the jsons
                jobs = None
                models: [LTLModel] = []
                for exp in data:
                    jobs = exp["jobs"]
                    if exp["category"] == "LTL":
                        model_template = LTLTemplate(exp["filteringMode"])
                        param = exp["parameterValue"]
                        inst_model = model_template.fill_template(param, attr_type=exp["attributeType"])
                        inst_model.to_lydia_backend()
                        models.append(inst_model)
                    else:
                        model_template = LTLTemplate(exp["filteringMode"])
                        source = exp["parameterValue"][0]
                        target = exp["parameterValue"][1]
                        inst_model = model_template.fill_template(source, target, attr_type=exp["attributeType"])
                        inst_model.to_lydia_backend()
                        models.append(inst_model)

                analyzer = LTLAnalyzer(event_log, models)
                times = []
                for j in range(iterations):
                    start = time.time()
                    df = analyzer.run_multiple_models(jobs=jobs, minimize_automaton=False)
                    end = time.time()
                    exec_time = end - start
                    print(exec_time)
                    times.append(exec_time)

                row = [log_name, filter_name, exp["category"], "multiple_models", f"{jobs}_job", np.mean(times)] + \
                      times + [inst_model.formula]
                writer = csv.writer(f)
                writer.writerow(row)
