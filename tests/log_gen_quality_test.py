from pyxdameraulevenshtein import damerau_levenshtein_distance, normalized_damerau_levenshtein_distance
from pm4py.objects.log.importer.xes import importer as xes_importer
import os
import numpy as np
import pdb

num_traces = 100
res_list = []
ascii_offset = 161

log = xes_importer.apply(os.path.join("test_logs", 'tele.xes'))
simplified_log = []
act_loc_set = set()
for trace in log:
    tmp_trace = ""
    for event in trace:
        activity_name = event['concept:name']
        act_loc_set.add(activity_name)
        tmp_trace += f"{activity_name}@"
    simplified_log.append(tmp_trace[:-1])

# Convert the activities and locations into ascii symbols for the string similarity
act_loc_list = list(act_loc_set)
symbol_to_ascii_map = {symbol: chr(idx + ascii_offset) for idx, symbol in enumerate(act_loc_list)}
ascii_simplified_log = []

for trace in simplified_log:
    tmp_trace = ""
    simplified_event_list = trace.split("@")
    for event_name in simplified_event_list:
        tmp_trace += symbol_to_ascii_map[event_name]
    # tmp_trace = trace
    # for symbol in symbol_to_ascii_map:
    #    tmp_trace = tmp_trace.replace(symbol, symbol_to_ascii_map[symbol])
    # ascii_simplified_log.append(tmp_trace.replace(",", "").replace(":", ""))
    ascii_simplified_log.append(tmp_trace)

distance_values = []
# Perform pairwise similarity
for tr_id_a, _ in enumerate(ascii_simplified_log):
    for tr_id_b in range(tr_id_a + 1, len(ascii_simplified_log)):
        distance_values.append(normalized_damerau_levenshtein_distance(ascii_simplified_log[tr_id_a],
                                                                       ascii_simplified_log[tr_id_b]))

res_list.append(np.mean(distance_values))
print(np.mean(distance_values), np.std(distance_values))