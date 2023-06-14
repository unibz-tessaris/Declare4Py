import time
import csv
import pdb
import sys
import os
import pathlib
SCRIPT_DIR = pathlib.Path("../", "src").resolve()
sys.path.append(os.path.dirname(SCRIPT_DIR))
from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.ConformanceChecking.LTLAnalyzer import LTLAnalyzer
from src.Declare4Py.ProcessModels.LTLModel import LTLTemplate

list_logs = ["InternationalDeclarations", "BPI_Challenge_2012", "DomesticDeclarations"]

simple_ltlf_templates = ["next_a", "eventuallya", "eventually_a_or_b", "eventually_a_then_b",
                         "eventually_a_next_b", "eventually_a_next_b_next_c", "eventually_a_then_b_then_c"]

tb_declare_templates = ['precedence', 'chain_precedence', 'responded_existence', 'chain_response',
                        'not_chain_precedence', 'not_chain_response', 'response', 'not_precedence', 'not_response',
                        'not_responded_existence', 'alternate_response', 'alternate_precedence']

simplt_ltl_model_params = {"InternationalDeclarations": [["Permit FINAL_APPROVED by SUPERVISOR"],
                                                         ["Permit FINAL_APPROVED by SUPERVISOR"],
                                                         ["Declaration SUBMITTED by EMPLOYEE",
                                                          "Declaration FINAL_APPROVED by SUPERVISOR"],
                                                         ["Declaration SUBMITTED by EMPLOYEE",
                                                          "Declaration FINAL_APPROVED by SUPERVISOR"],
                                                         ["Declaration SUBMITTED by EMPLOYEE",
                                                          "Declaration FINAL_APPROVED by SUPERVISOR"],
                                                         ["End trip", "Permit FINAL_APPROVED by SUPERVISOR",
                                                          "Declaration SUBMITTED by EMPLOYEE"],
                                                         ["End trip", "Permit FINAL_APPROVED by SUPERVISOR",
                                                          "Declaration SUBMITTED by EMPLOYEE"]],
                           "BPI_Challenge_2012": [["A_SUBMITTED"],
                                                  ["A_SUBMITTED"],
                                                  ["A_SUBMITTED", "A_PARTLYSUBMITTED"],
                                                  ["A_SUBMITTED", "A_PARTLYSUBMITTED"],
                                                  ["A_SUBMITTED", "A_PARTLYSUBMITTED"],
                                                  ["A_SUBMITTED", "A_PARTLYSUBMITTED", "A_PREACCEPTED"],
                                                  ["A_SUBMITTED", "A_PARTLYSUBMITTED", "A_PREACCEPTED"],
                                                  ]}
source_list_2 = {"InternationalDeclarations": ["Declaration SUBMITTED by EMPLOYEE",
                                               "Declaration FINAL_APPROVED by SUPERVISOR"],
                 "BPI_Challenge_2012": ['A_SUBMITTED', 'A_PARTLYSUBMITTED']}
target_list_2 = {"InternationalDeclarations": ["End trip", "Request Payment"],
                 "BPI_Challenge_2012": ['A_PREACCEPTED', 'W_Completeren aanvraag']}

target_list_7 = {"Sepsis Cases": ["Leucocytes", "Release A", "ER Registration"],
                 "InternationalDeclarations": ["Declaration SUBMITTED by EMPLOYEE", "End trip", "Request Payment",
                                               "Payment Handled", "Permit FINAL_APPROVED by SUPERVISOR", "Start trip",
                                               "Permit FINAL_APPROVED by DIRECTOR"],
                 "BPI_Challenge_2012": ['A_PREACCEPTED', 'W_Completeren aanvraag', 'A_ACCEPTED', 'O_SENT_BACK',
                                        'A_REGISTERED', 'A_APPROVED', 'W_Valideren aanvraag']}
source_list_7 = {"InternationalDeclarations": ["Permit FINAL_APPROVED by SUPERVISOR",
                                               "Permit FINAL_APPROVED by DIRECTOR",
                                               "Payment Handled",
                                               "Declaration APPROVED by ADMINISTRATION",
                                               "Request Payment",
                                               "Declaration SUBMITTED by EMPLOYEE",
                                               "Permit SUBMITTED by EMPLOYEE"],
                 "BPI_Challenge_2012": ['A_SUBMITTED', 'W_Nabellen offertes', 'A_PARTLYSUBMITTED', 'O_SELECTED',
                                        'O_SENT', 'A_FINALIZED', 'O_CREATED']}

template_family = "Simple LTLf templates"  # 'TB-DECLARE templates'
template_family = "TB-DECLARE templates"
template_list = simple_ltlf_templates if template_family == "Simple LTLf templates" else tb_declare_templates
len_TB_disjunctions = 5  # 2 Or 5
jobs = 4
iterations = 5

if __name__ == "__main__":
    with open(os.path.join("test_performance", "ltl_analyzer.csv"), 'a') as f:
        for log_name in list_logs:

            log_path = os.path.join("test_logs", f"{log_name}.xes.gz")
            event_log = D4PyEventLog(case_name="case:concept:name")
            event_log.parse_xes_log(log_path)
            """
            event_log.get_event_attribute_values("concept:name")

            trace_lengths = []
            num_events = 0
            for trace in event_log.log:
                trace_lengths.append(len(trace))
                num_events += len(trace)

            import numpy as np
            print(num_events)
            print(np.max(trace_lengths))
            print(np.min(trace_lengths))
            print(np.median(trace_lengths))
            pdb.set_trace()
            """





            for i, template in enumerate(template_list):
                print(f"Running {log_name} with {template} ...")
                model_template = LTLTemplate(template)
                if template_family == "Simple LTLf templates":
                    param = simplt_ltl_model_params[log_name][i]
                    initialized_ltl_model = model_template.fill_template(param)
                else:
                    if len_TB_disjunctions == 2:
                        initialized_ltl_model = model_template.fill_template(source_list_2[log_name],
                                                                             target_list_2[log_name])
                    else:
                        initialized_ltl_model = model_template.fill_template(source_list_7[log_name],
                                                                             target_list_7[log_name])
                # analyzer = LTLAnalyzer(event_log.to_dataframe(), initialized_ltl_model)
                # initialized_ltl_model.to_ltlf2dfa_backend()
                initialized_ltl_model.to_lydia_backend()
                analyzer = LTLAnalyzer(event_log, initialized_ltl_model)
                times = []
                for j in range(iterations):
                    start = time.time()
                    df = analyzer.run(jobs=jobs)
                    end = time.time()
                    exec_time = end - start
                    times.append(exec_time)
                writer = csv.writer(f)
                writer.writerow([log_name, "no_group_by", f"{jobs}_job", template_family, len_TB_disjunctions, template]
                                + times)
