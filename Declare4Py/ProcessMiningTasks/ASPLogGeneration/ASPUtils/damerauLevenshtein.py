import pandas as pd
from typing import List, Set, Dict


class DamerauLevenshteinDistance:

    @staticmethod
    def analize_csv(path: str) -> float:

        ascii_offset: int = 161
        df: pd.DataFrame = pd.read_csv(path)[["case:concept:name", "concept:name"]]

        act_loc_set: Set = set(df["concept:name"].unique())
        symbol_to_ascii_map: Dict[str, chr] = {symbol: chr(idx + ascii_offset) for idx, symbol in enumerate(list(act_loc_set))}

        case: int = 0
        traces: List[str] = []
        trace: str = ""

        for _, row in df.iterrows():
            if row["case:concept:name"] == f"case_{case}":
                trace += symbol_to_ascii_map[row["concept:name"]]
            else:
                traces.append(trace)
                trace = symbol_to_ascii_map[row["concept:name"]]
                case += 1
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