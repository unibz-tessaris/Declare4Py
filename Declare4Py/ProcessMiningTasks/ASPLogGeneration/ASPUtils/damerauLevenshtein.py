import pandas as pd
from typing import List, Set, Dict
import pm4py
import os

class DamerauLevenshteinDistance:

    @staticmethod
    def analize_csv_from_xes(path: str) -> float:
        log = pm4py.read_xes(path)
        pd = pm4py.convert_to_dataframe(log)
        pd.to_csv(path[:-4] + ".csv", index=False)
        return DamerauLevenshteinDistance.analize_csv(path[:-4] + ".csv")

    @staticmethod
    def analize_csv(path: str) -> float:

        ascii_offset: int = 161
        df: pd.DataFrame = pd.read_csv(path)[["case:concept:name", "concept:name"]]

        act_loc_set: Set = set(df["concept:name"].unique())
        symbol_to_ascii_map: Dict[str, chr] = {symbol: chr(idx + ascii_offset) for idx, symbol in enumerate(list(act_loc_set))}

        traces: List[str] = []
        trace: str = ""

        current_case = None
        for _, row in df.iterrows():

            if current_case is None:
                current_case = row["case:concept:name"]

            if row["case:concept:name"] == current_case:
                trace += symbol_to_ascii_map[row["concept:name"]]
            else:
                traces.append(trace)
                current_case = row["case:concept:name"]
                trace = symbol_to_ascii_map[row["concept:name"]]

        traces.append(trace)

        count: int = 0
        distance: int = 0
        for i in range(len(traces)):
            for j in range(i + 1, len(traces)):
                count += 1
                distance += DamerauLevenshteinDistance.optimal_string_alignment_distance(traces[i], traces[j])

        return distance/count


    @staticmethod
    def optimal_string_alignment_distance(s1: str, s2: str) -> int:
        # Create a table to store the results of subproblems
        dp = [[0 for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]

        # Initialize the table
        for i in range(len(s1) + 1):
            dp[i][0] = i
        for j in range(len(s2) + 1):
            dp[0][j] = j

        # Populate the table using dynamic programming
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

        # Return the edit distance
        return dp[len(s1)][len(s2)]

"""
if __name__ == "__main__":

    path = "C:\\Users\\Matteo\\Desktop\\"
    file = "Rum_test_20_tracce"

    val = DamerauLevenshteinDistance.analize_csv_from_xes(path + file + ".xes")
    os.rename(f"{path}{file}.csv", f"{path}distance_{round(val, 4)}_{file}.csv")

    for file in ["rum_test1", "rum_test2", "rum_test3", "rum_test4", "rum_test5"]:

        val = DamerauLevenshteinDistance.analize_csv_from_xes(path + file + ".xes")
        os.rename(f"{path}{file}.csv", f"{path}similarity_{round(val, 4)}_{file}.csv")"""
