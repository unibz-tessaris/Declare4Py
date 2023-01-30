from __future__ import annotations

import pandas as pd
import pm4py
import packaging
from packaging import version
from mlxtend.frequent_patterns import fpgrowth, apriori
from mlxtend.preprocessing import TransactionEncoder
from pm4py.objects.log import obj as lg
from pm4py.objects.log.obj import EventLog, Trace
from typing import Union, Set, List, Tuple, Any, Dict


class LogAnalyzer:
    """
        Wrapper that collects the input log, the computed binary encoding and frequent item sets
        for the input log.

        Attributes
        ----------
        log : EventLog
            the input event log parsed from a XES file
        log_length : int
            the trace number of the input log
        frequent_item_sets : DataFrame
            list of the most frequent item sets found along the log traces, together with their support and length
        binary_encoded_log : DataFrame
                the binary encoded version of the input log
    """

    def __init__(self):
        self.log: lg.EventLog | None = None
        self.log_length = None
        self.frequent_item_sets = None
        self.binary_encoded_log = None

    # LOG MANAGEMENT UTILITIES
    def get_trace_keys(self) -> list[tuple[int, str]]:
        """
        Return the name of each trace, along with the position in the log.

        Returns
        -------
        trace_ids
            list containing the position in the log and the name of the trace.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        trace_ids = []
        for trace_id, trace in enumerate(self.log):
            trace_ids.append((trace_id, trace.attributes["concept:name"]))
        return trace_ids

    def parse_xes_log(self, log_path: str) -> None:
        """
        Set the 'log' EventLog object and the 'log_length' integer by reading and parsing the log corresponding to
        given log file path.

        Parameters
        ----------
        :param log_path : str
            File path where the log is stored.
        """
        if packaging.version.parse(pm4py.__version__) > packaging.version.Version("2.3.1"):
            read_log = pm4py.read_xes(log_path)
            self.log = pm4py.convert_to_event_log(read_log)
            self.log_length = len(self.log)
        else:
            # Mettere qui eventuale conversione da pandas frame a EventLog
            raise RuntimeError("Please use the newer version of pm4py")

    def activities_log_projection(self) -> list[list[str]]:
        """
        Return for each trace a time-ordered list of the activity names of the events.

        Returns
        -------
        projection
            nested lists, the outer one addresses traces while the inner one contains event activity names.
        """
        projection = []
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        for trace in self.log:
            tmp_trace = []
            for event in trace:
                tmp_trace.append(event["concept:name"])
            projection.append(tmp_trace)
        return projection

    def resources_log_projection(self) -> list[list[str]]:
        """
        Return for each trace a time-ordered list of the resources of the events.

        Returns
        -------
        projection
            nested lists, the outer one addresses traces while the inner one contains event activity names.
        """
        projection = []
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        for trace in self.log:
            tmp_trace = []
            for event in trace:
                tmp_trace.append(event["org:group"])
            projection.append(tmp_trace)
        return projection

    def compute_frequent_itemsets(self, min_support: float, dimension: str = 'act', algorithm: str = 'fpgrowth',
                                  len_itemset: int = None) -> None:
        """
        Compute the most frequent item sets with a support greater or equal than 'min_support' with the given algorithm
        and over the given dimension.

        Parameters
        ----------
        :param min_support: float
            the minimum support of the returned item sets.
        :param dimension : str, optional
            choose 'act' to perform the encoding over activity names, 'payload' over resources (default 'act').
        :param algorithm : str, optional
            the algorithm for extracting frequent itemsets, choose between 'fpgrowth' (default) and 'apriori'.
        :param len_itemset : int, optional
            the maximum length of the extracted itemsets.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        if not 0 <= min_support <= 1:
            raise RuntimeError("Min. support must be in range [0, 1].")

        self.log_encoding(dimension)
        if algorithm == 'fpgrowth':
            frequent_itemsets = fpgrowth(self.binary_encoded_log, min_support=min_support, use_colnames=True)
        elif algorithm == 'apriori':
            frequent_itemsets = apriori(self.binary_encoded_log, min_support=min_support, use_colnames=True)
        else:
            raise RuntimeError(f"{algorithm} algorithm not supported. Choose between fpgrowth and apriori")
        frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
        if len_itemset is None:
            self.frequent_item_sets = frequent_itemsets
        elif len_itemset < 1:
            raise RuntimeError(f"The parameter len_itemset must be greater than 0.")
        else:
            self.frequent_item_sets = frequent_itemsets[(frequent_itemsets['length'] <= len_itemset)]

    def get_log(self) -> pm4py.objects.log.obj.EventLog:
        """
        Return the log previously fed in input.

        Returns
        -------
        log
            the input log.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        return self.log

    def get_length(self) -> int:
        """
        Return the length of the log, which was previously fed in input.

        Returns
        -------
        log_length
            the length of the log.
        """
        if self.log_length is None:
            raise RuntimeError("You must load a log before.")
        return self.log_length

    def get_log_alphabet_payload(self) -> set[str]:
        """
        Return the set of resources that are in the log.

        Returns
        -------
        resources
            resource set.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        resources = set()
        for trace in self.log:
            for event in trace:
                resources.add(event["org:group"])
        return resources

    def get_log_alphabet_activities(self):
        """
        Return the set of activities that are in the log.

        Returns
        -------
        activities
            activity set.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        activities = set()
        for trace in self.log:
            for event in trace:
                activities.add(event["concept:name"])
        return list(activities)

    def get_frequent_item_sets(self):
        """
        Return the most frequent item sets.

        Returns
        -------
        frequent_item_sets
            set of the most frequent items.
        """
        if self.frequent_item_sets is None:
            raise RuntimeError("Please run the compute_frequent_itemsets function first.")
        return self.frequent_item_sets

    def log_encoding(self, dimension: str = 'act') -> pd.DataFrame:
        """
        Return the log binary encoding, i.e. the one-hot encoding stating whether an attribute is contained
        or not inside each trace of the log.

        Parameters
        ----------
        :param dimension : str, optional
            choose 'act' to perform the encoding over activity names, 'payload' over resources (default 'act').

        Returns
        -------
        binary_encoded_log
            the one-hot encoding of the input log, made over activity names or resources depending on 'dimension' value.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        te = TransactionEncoder()
        if dimension == 'act':
            dataset = self.activities_log_projection()
        elif dimension == 'payload':
            dataset = self.resources_log_projection()
        else:
            raise RuntimeError(f"{dimension} dimension not supported. Choose between 'act' and 'payload'")
        te_ary = te.fit(dataset).transform(dataset)
        self.binary_encoded_log = pd.DataFrame(te_ary, columns=te.columns_)
        return self.binary_encoded_log

    def get_binary_encoded_log(self) -> pd.DataFrame:
        """
        Return the one-hot encoding of the log.

        Returns
        -------
        binary_encoded_log
            the one-hot encoded log.
        """
        if self.log is None:
            raise RuntimeError("You must load a log before.")
        if self.frequent_item_sets is None:
            raise RuntimeError("You must run the item set extraction algorithm before.")

        return self.binary_encoded_log

    # LOG FILTER FUNCTIONS
    def filter_time_range_contained(self, start_date: str, end_date: str, mode: str = "events",
                                    timestamp_key: str = "time:timestamp",
                                    case_id_key: str = "case:concept:name") -> EventLog:

        """
        Description
        -----------
        This function uses the get_log() of the declare4py package.

        Parameters
        ----------
        :param self: declare4py obj
        :param start_date: str in form year-month-day hours:minutes:seconds. E.g.: 2013-01-01 00:00:00
        :param end_date: str in form year-month-day hours:minutes:seconds. E.g.: 2013-01-01 00:00:00
        :param case_id_key: attribute to be used as case identifier
        :param timestamp_key: attribute to be used for the timestamp
        :param mode: define which of the three modes wil be set: events, traces_intersecting and traces_contained

        Returns
        -------
        :rtype: EventLog
        Returns the filtered log in the timeframe.

        """
        return pm4py.filter_time_range(self.log, start_date, end_date, mode, timestamp_key, case_id_key)

    def filter_case_performance(self, min_performance: float, max_performance: float,
                                timestamp_key: str = "time:timestamp",
                                case_id_key: str = "case:concept:name") -> EventLog:
        """
        Description
        -----------
        Filters the log using two integers values, which are the performance of the event

        Parameters
        ----------
        :param self: the LogAnalyser object containing the d4py log
        :param min_performance: minimum allowed case duration
        :param max_performance: maximum allowed case duration
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: EventLog
        Returns the filtered log containing cases in the range of the specified performance interval.
        """
        return pm4py.filter_case_performance(self.log, min_performance, max_performance, timestamp_key,
                                             case_id_key)

    def get_start_activities(self, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp",
                             case_id_key: str = "case:concept:name") -> Dict[str, int]:
        """
        Description
        -----------
        Retrieves all starting activities of the log

        Parameters
        ----------
        :param self: the LogAnalyser object containing the d4py log
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: Dict[str, int]
        Returns a dictionary containing all start activities.

        """
        return pm4py.get_start_activities(self.log, activity_key, timestamp_key, case_id_key)

    def filter_start_activities(self, activities: Union[Set[str], List[str]], retain: bool = True,
                                activity_key: str = "concept:name",
                                timestamp_key: str = "time:timestamp",
                                case_id_key: str = "case:concept:name") -> EventLog:
        """
        Description
        -----------
        Filters all activities that start with the specified start activities

        Parameters
        ----------
        :param self: the LogAnalyser object containing the d4py log
        :param activities: Union[set[str], list[str]] Collection of start activities
        :param retain: if True, we retain the traces containing the given start activities, if false, we drop the traces
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: EventLog
        Returns filtered log that contains cases having a start activities in the specified list.

        """
        return pm4py.filter_start_activities(self.log, activities, retain, activity_key, timestamp_key,
                                             case_id_key)

    def get_end_activities(self, activity_key: str = "concept:name",
                           timestamp_key: str = "time:timestamp",
                           case_id_key: str = "case:concept:name") -> Dict[str, int]:
        """
        Description
        -----------
        Returns the end activities of a log

        Parameters
        ----------
        :param self: the LogAnalyser object containing the d4py log
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: Dict[str, int]
        Returns a dictionary containing all end activities.
        """
        return pm4py.get_end_activities(self.log, activity_key, timestamp_key, case_id_key)

    def filter_end_activities(self, activities: [Set[str], List[str]], retain: bool = True,
                              activity_key: str = "concept:name",
                              timestamp_key: str = "time:timestamp",
                              case_id_key: str = "case:concept:name"):
        """

        Description
        -----------
        Filter cases having an end activity in the provided list

        Parameters
        ---------
        :param self: declare4py obj
        :param activities: collection of end activities
        :param retain: if True, we retain the traces containing the given end activities, if false, we drop the traces
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        Returns filtered log containing cases having an end activity in the provided list.
        """
        return pm4py.filter_end_activities(self.log, activities, retain, activity_key, timestamp_key, case_id_key)

    def get_variants(self, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp",
                     case_id_key: str = "case:concept:name") -> Dict[Tuple[str], List[Trace]]:
        """

        Description
        -----------
        Retrieves all variants from the log.

        Parameters
        ---------
        :param self: declare4py obj
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: Dict[Tuple[str], List[Trace]]
        Returns a dictionary containing all variants in the log.
        """
        return pm4py.get_variants(self.log, activity_key, timestamp_key, case_id_key)

    def filter_variants_top_k(self, k: int, activity_key: str = "concept:name", timestamp_key: str = "time:timestamp",
                              case_id_key: str = "case:concept:name") -> EventLog:
        """

        Description
        -----------
        Keeps the top-k variants of the log.

        Parameters
        ---------
        :param self: declare4py obj
        :param k: number of variants that should be kept
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: EventLog
        Returns log containing top-k variants.
        """
        return pm4py.filter_variants_top_k(self.log, k, activity_key, timestamp_key, case_id_key)

    def filter_variants(self, variants: [Set[str], List[str]], retain: bool = True, activity_key: str = "concept:name",
                        timestamp_key: str = "time:timestamp",
                        case_id_key: str = "case:concept:name") -> EventLog:
        """

        Description
        -----------
        Filter a log by a specified set of variants.

        Parameters
        ---------
        :param self: declare4py obj
        :param variants: collection of variants to filter;
        A variant should be specified as a list of tuples of activity names, e.g., [('a', 'b', 'c')]
        :param retain: boolean;
        if True all traces conforming to the specified variants are retained; if False, all those traces are removed
        :param activity_key: attribute to be used for the activity
        :param timestamp_key: attribute to be used for the timestamp
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: EventLog
        Returns filtered log on specified variants.
        """
        return pm4py.filter_variants(self.log, variants, retain, activity_key, timestamp_key, case_id_key)

    def get_event_attribute_values(self, attribute: str, count_once_per_case: bool = False,
                                   case_id_key: str = "case:concept:name") -> Dict[str, int]:
        """

        Description
        -----------
        Returns the values for a specified (event) attribute.

        Parameters
        ---------
        :param self: Log object
        :param attribute: attribute
        :param count_once_per_case: If True, consider only an occurrence of the given attribute value inside a case
        (if there are multiple events sharing the same attribute value, count only 1 occurrence)
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: Dict[str, int]
        Returns filtered log on specified variants.
        """

        return pm4py.get_event_attribute_values(self.log, attribute, count_once_per_case, case_id_key)

    def filter_event_attribute_values(self, attribute_key: str, values: Union[Set[str], List[str]], level: str = "case",
                                      retain: bool = True, case_id_key: str = "case:concept:name") -> EventLog:
        """

        Description
        -----------
        Filter an event log on the values of some event attribute.

        Parameters
        ---------
        :param attribute_key: attribute to filter
        :param values: admitted (or forbidden) values
        :param level: specifies how the filter should be applied
        ('case' filters the cases where at least one occurrence happens, 'event' filter the events eventually
            trimming the cases)
        :param retain: specifies if the values should be kept or removed
        :param case_id_key: attribute to be used as case identifier

        Returns
        -------
        :rtype: EventLog
        Returns filtered eventlog object on the values of some event attribute.
        """

        return pm4py.filter_event_attribute_values(self.log, attribute_key, values, level, retain, case_id_key)
