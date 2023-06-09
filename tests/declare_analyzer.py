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

# event_log = D4PyEventLog()
iterations = 5

list_logs = ["InternationalDeclarations", "Sepsis Cases"]
# list_logs = ["Sepsis Cases"]
simple_ltlf_templates = ["next_a", "eventually_activity_a", "eventually_a_or_b", "eventually_a_then_b",
                         "eventually_a_next_b", "eventually_a_next_b_next_c", "eventually_a_then_b_then_c"]

tb_declare_templates = ['responded_existence', 'response', 'alternate_response', 'chain_response', 'precedence',
                        'alternate_precedence', 'chain_precedence', 'not_responded_existence', 'not_response',
                        'not_precedence', 'not_chain_response', 'not_chain_precedence']

simplt_ltl_model_params = {"Sepsis Cases": [["ER Triage"],
                                     ["ER Triage"],
                                     ["ER Triage", "CRP"],
                                     ["ER Triage", "CRP"],
                                     ["ER Triage", "CRP"],
                                     ["ER Triage", "CRP", "LacticAcid"],
                                     ["ER Triage", "CRP", "LacticAcid"]],
                    "InternationalDeclarations": [["Permit FINAL_APPROVED by SUPERVISOR"],
                                                  ["Permit FINAL_APPROVED by SUPERVISOR"],
                                                  ["Declaration SUBMITTED by EMPLOYEE", "Declaration FINAL_APPROVED by SUPERVISOR"],
                                                  ["Declaration SUBMITTED by EMPLOYEE", "Declaration FINAL_APPROVED by SUPERVISOR"],
                                                  ["Declaration SUBMITTED by EMPLOYEE", "Declaration FINAL_APPROVED by SUPERVISOR"],
                                                  ["End trip", "Permit FINAL_APPROVED by SUPERVISOR",
                                                   "Declaration SUBMITTED by EMPLOYEE"],
                                                  ["End trip", "Permit FINAL_APPROVED by SUPERVISOR", "Declaration SUBMITTED by EMPLOYEE"]]}
source_list_2 = {"Sepsis Cases": ["ER Triage", "CRP"],
                 "InternationalDeclarations": ["Declaration SUBMITTED by EMPLOYEE",
                                               "Declaration FINAL_APPROVED by SUPERVISOR"]}
target_list_2 = {"Sepsis Cases": ["Leucocytes", "Release A"],
                 "InternationalDeclarations": ["End trip", "Request Payment"]}
source_list_3 = {"Sepsis Cases": ["ER Triage", "LacticAcid", "CRP"],
                 "InternationalDeclarations": ["Permit FINAL_APPROVED by SUPERVISOR",
                                               "Declaration SUBMITTED by EMPLOYEE",
                                               "Declaration FINAL_APPROVED by SUPERVISOR"]}
target_list_3 = {"Sepsis Cases": ["Leucocytes", "Release A", "ER Registration"],
                 "InternationalDeclarations": ["End trip", "Request Payment", "Payment Handled"]}
template_family = "Simple LTLf templates" # 'TB-DECLARE templates'
#template_family = "TB-DECLARE templates"
template_list = simple_ltlf_templates if template_family == "Simple LTLf templates" else tb_declare_templates
len_TB_disjunctions = "-"
jobs = 1

if __name__ == "__main__":
    with open(os.path.join("test_performance", "ltl_analyzer.csv"), 'a') as f:
        for log_name in list_logs:

            log_path = os.path.join("test_logs", f"{log_name}.xes.gz")
            event_log = D4PyEventLog(case_name="case:concept:name")
            event_log.parse_xes_log(log_path)

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
                        initialized_ltl_model = model_template.fill_template(source_list_3[log_name],
                                                                             target_list_3[log_name])
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
                    # df.to_csv("lydia.csv") #ltlf2dfa lydia
                    times.append(exec_time)
                writer = csv.writer(f)
                writer.writerow([log_name, "no_group_by", f"{jobs}_job", template_family, len_TB_disjunctions, template]
                                + times)
