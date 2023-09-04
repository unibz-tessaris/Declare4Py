import pdb
import os
import matplotlib
from matplotlib import pyplot as plt
import pandas as pd

plt.rc('font', family='serif', serif='Times')
plt.rc('text', usetex=True)
plt.rc('xtick', labelsize=17)
plt.rc('axes', titlesize=21)
plt.rc('legend', fontsize=15)
plt.rc('ytick', labelsize=17)
plt.rc('axes', labelsize=17)
plt.rc('lines', linewidth=2, markersize=8, markeredgecolor='black')

model_checking_data_len = [17, 34, 51, 69]
model_checking_data_d4py = [0.2324790954589843, 2.3160719871520996, 2.7095189094543457, 3.0642449855804443]
model_checking_data_rum = [0.527, 2.583, 3.573, 4.040]

discovery_no_data_len = [0.2, 0.4, 0.6, 0.8]
discovery_no_data_d4py = [32.231475830078125, 28.104568004608154, 26.241751194000244, 11.41601300239563]

query_1_nodata_d4py = [0.42098116874694824, 0.4873671531677246, 0.528853178024292, 0.531684160232544]
query_2_nodata_d4py = [2.6443979740142822, 3.0853519439697266, 3.3742330074310303, 3.5121097564697266]

fig = plt.figure()
"""
plt.plot(model_checking_data_len, model_checking_data_rum, ls='-.', c='forestgreen', label="RuM", marker='>')
plt.plot(model_checking_data_len, model_checking_data_d4py, ls='-', c='mediumorchid', label="Declare4Py", marker='D')
plt.legend()
plt.title("Conformance checking")
plt.xlabel("Number of model constraints")
plt.ylabel("Time [s]")
plt.tight_layout()
fig.savefig(f"conformance_checking.pdf")
fig.clear()

plt.plot(discovery_no_data_len, discovery_no_data_d4py, ls='-', c='mediumorchid', label="Declare4Py", marker='D')
plt.title("Model discovery")
plt.xlabel("Itemset support")
plt.ylabel("Time [s]")
plt.tight_layout()
fig.savefig(f"model_discovery.pdf")
fig.clear()

plt.plot(discovery_no_data_len, query_1_nodata_d4py, ls='-', c='mediumorchid',  label="1 variable", marker='D')
plt.plot(discovery_no_data_len, query_2_nodata_d4py, ls=':', c='darkorchid',  label="2 variables", marker='^')
plt.legend(loc="upper left")

plt.title("Query checking")
plt.xlabel("Declare constraint support")
plt.ylabel("Time [s]")
plt.tight_layout()
fig.savefig(f"query_checking.pdf")
"""

"""
# PLOT ltl analyzer performance
"""
data_ltl_checker = pd.read_csv("test_performance/ltl_analyzer.csv", names=["dataset", "type", "jobs", "template_family",
                                                                           "length_or", "constraint", "t1", "t2", "t3",
                                                                           "t4", "t5"])
list_logs = ["InternationalDeclarations", "BPI_Challenge_2012"]
log_name = {"InternationalDeclarations": "International Declarations", "BPI_Challenge_2012": "BPIC 2012"}

for log in list_logs:
    for templates in ["TB-DECLARE", "Simple LTLf"]:
        if templates == "TB-DECLARE":
            template_indices = ["P", "chP", "rE", "chR", "nChP", "nChR", "R", "nP", "nR", "nRE", "aR", "aP"]
            for length_or in ["2", "5"]:
                parallel_4_df = data_ltl_checker[(data_ltl_checker["dataset"] == log) &
                                                 (data_ltl_checker["jobs"] == '4_job') &
                                                 (data_ltl_checker["length_or"] == length_or)]
                sequential_df = data_ltl_checker[(data_ltl_checker["dataset"] == log) &
                                                 (data_ltl_checker["jobs"] == '1_job') &
                                                 (data_ltl_checker["length_or"] == length_or)]
                results_4_parallel = parallel_4_df[["t1", "t2", "t3", "t4", "t5"]].mean(axis=1)
                results_sequential = sequential_df[["t1", "t2", "t3", "t4", "t5"]].mean(axis=1)

                df = pd.DataFrame({'4 jobs': results_4_parallel.values, '1 job': results_sequential.values},
                                  index=template_indices)
                ax = df.plot.bar(rot=45, color={"4 jobs": "mediumorchid", "1 job": "mediumblue"}, edgecolor='black')

                plt.legend(loc="upper left")
                plt.title(f"{log_name[log]}, {length_or}-{templates}")
                plt.xlabel(f"{templates} Template ids")
                plt.ylabel("Time [s]")
                plt.tight_layout()
                fig = ax.get_figure()
                fig.savefig(os.path.join("test_performance", f"{log}_{templates}_conf_check_{length_or}.pdf"))
                fig.clear()
        else:
            template_indices = ["Xa", "Fa", "FaORFb", "F(aFb)", "F(aXb)", "F(aX(bXc))", "F(aF(bFc))"]
            parallel_4_df = data_ltl_checker[(data_ltl_checker["dataset"] == log) &
                                             (data_ltl_checker["jobs"] == '4_job') &
                                             (data_ltl_checker["length_or"] == "-")]
            sequential_df = data_ltl_checker[(data_ltl_checker["dataset"] == log) &
                                             (data_ltl_checker["jobs"] == '1_job') &
                                             (data_ltl_checker["length_or"] == "-")]
            results_4_parallel = parallel_4_df[["t1", "t2", "t3", "t4", "t5"]].mean(axis=1)
            results_sequential = sequential_df[["t1", "t2", "t3", "t4", "t5"]].mean(axis=1)

            df = pd.DataFrame({'4 jobs': results_4_parallel.values, '1 job': results_sequential.values},
                              index=template_indices)
            ax = df.plot.bar(rot=45, color={"4 jobs": "mediumorchid", "1 job": "mediumblue"}, edgecolor='black')

            plt.legend(loc="upper left")
            plt.title(f"{log_name[log]}, {templates}")
            plt.xlabel(f"{templates} Template ids")
            plt.ylabel("Time [s]")
            plt.tight_layout()
            fig = ax.get_figure()
            fig.savefig(os.path.join("test_performance", f"{log}_{templates}_conf_check.pdf"))
            fig.clear()
