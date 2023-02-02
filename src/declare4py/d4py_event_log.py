from __future__ import annotations

import packaging
from packaging import version

from mlxtend.frequent_patterns import fpgrowth, apriori

import pm4py
from pm4py.objects.log.obj import EventLog

from typing import Union, List, Tuple, Set

from src.declare4py.encodings import AggregateTransformer

from pandas import DataFrame


class D4PyEventLog:
    """
    Wrapper that collects the input log, the computed binary encoding and frequent item set for the input log.

    Args:
        log: the input event log parsed from a XES file
        log_length: the trace number of the input log
        frequent_item_sets: list of the most frequent item sets found along the log traces, together with their support and length
    """

    def __init__(self):
        """The class constructor

        Example::

            d4py_log = D4PyEventLog()
        """
        self.log: Union[EventLog, None] = None
        self.log_length: Union[int, None] = None
        self.frequent_item_sets: Union[DataFrame, None] = None

    # LOG MANAGEMENT UTILITIES
    def parse_xes_log(self, log_path: str) -> None:
        """
        Set the 'log' EventLog object and the 'log_length' integer by reading and parsing the log corresponding to
        given log file path.

        Note:
            the current version of Declare4py supports only (zipped) XES format of the event logs.

        Args:
            log_path: File path where the log is stored.

        Example::

            log_path = path/to/my/xes
            d4py_log = D4PyEventLog()
            d4py_log.parse_xes_log(log_path)
        """
        if packaging.version.parse(pm4py.__version__) > packaging.version.Version("2.3.1"):
            read_log = pm4py.read_xes(log_path)
            self.log = pm4py.convert_to_event_log(read_log)
            self.log_length = len(self.log)
        else:
            # Mettere qui eventuale conversione da pandas frame a EventLog
            raise RuntimeError("Please use the newer version of pm4py")

    def get_log(self) -> EventLog:
        """
        Returns the log previously fed in input.

        Returns:
            the input log.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        return self.log

    def get_length(self) -> int:
        """
        Return the length of the log, which was previously fed in input.

        Returns:
            the length of the log.
        """
        if self.log_length is None:
            raise RuntimeError("You must load a log before.")
        return self.log_length

    def get_log_alphabet_attribute(self, attribute_name: str = None) -> Set[str]:
        """
        Return the set of values for a given input attribute of the case.

        Args:
            attribute_name: the name of the attribute

        Returns:
            resource set.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        resources = set()
        for trace in self.log:
            for event in trace:
                resources.add(event[attribute_name])
        return resources

    def get_trace_keys(self) -> List[Tuple[int, str]]:
        """
        Returns the name of each trace, along with the position in the log.

        Returns:
            a list containing the position in the log and the name of the trace.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        trace_ids = []
        for trace_id, trace in enumerate(self.log):
            trace_ids.append((trace_id, trace.attributes["concept:name"]))
        return trace_ids

    def attribute_log_projection(self, attribute_name: str = None) -> List[List[str]]:
        """
        Returns for each trace a time-ordered list of the values of the input attribute for each event.

        Returns:
            nested lists, the outer one addresses traces while the inner one contains event activity names.
        """
        projection = []
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        for trace in self.log:
            tmp_trace = []
            for event in trace:
                tmp_trace.append(event[attribute_name])
            projection.append(tmp_trace)
        return projection

    def compute_frequent_itemsets(self, min_support: float, case_id_col: str, categorical_attributes: List[str] = None,
                                  algorithm: str = 'fpgrowth', len_itemset: int = 2) -> None:
        """
        Compute the most frequent item sets with a support greater or equal than 'min_support' with the given algorithm
        and over the given dimension.

        Args:
            min_support: the minimum support of the returned item sets.
            case_id_col: the name of the log attribute containing the ids of the cases
            categorical_attributes: a list of strings containing the names of the attributes to be encoded. For example, 'concept:name' for the activity names and 'org:group' for the resources.
            algorithm: the algorithm for extracting frequent itemsets, choose between 'fpgrowth' (default) and 'apriori'.
            len_itemset: the maximum length of the extracted itemsets.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        if not 0 <= min_support <= 1:
            raise RuntimeError("Min. support must be in range [0, 1].")

        log_df = pm4py.convert_to_dataframe(self.log)
        for attr_name in categorical_attributes:
            if attr_name not in log_df.columns:
                raise RuntimeError(f"{attr_name} is not a valid attribute. Check the log.")

        encoder: AggregateTransformer = AggregateTransformer(case_id_col=case_id_col, cat_cols=categorical_attributes,
                                                             num_cols=[], boolean=True)
        binary_encoded_log = encoder.fit_transform(log_df)
        if algorithm == 'fpgrowth':
            frequent_itemsets = fpgrowth(binary_encoded_log, min_support=min_support, use_colnames=True)
        elif algorithm == 'apriori':
            frequent_itemsets = apriori(binary_encoded_log, min_support=min_support, use_colnames=True)
        else:
            raise RuntimeError(f"{algorithm} algorithm not supported. Choose between fpgrowth and apriori")
        frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
        if len_itemset is None:
            self.frequent_item_sets = frequent_itemsets
        elif len_itemset < 1:
            raise RuntimeError(f"The parameter len_itemset must be greater than 0.")
        else:
            self.frequent_item_sets = frequent_itemsets[(frequent_itemsets['length'] <= len_itemset)]

    def get_frequent_item_sets(self):
        """
        Return the most frequent item sets.

        Returns:
            set of the most frequent items.
        """
        if self.frequent_item_sets is None:
            raise RuntimeError("Please run the compute_frequent_itemsets function first.")
        return self.frequent_item_sets
