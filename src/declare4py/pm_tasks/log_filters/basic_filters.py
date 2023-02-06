from src.declare4py.d4py_event_log import D4PyEventLog

import pm4py
from pm4py.objects.log.obj import EventLog, Trace
from typing import Union, Set, List, Tuple, Any, Dict


class BasicFilters:

    def __init__(self, event_log: D4PyEventLog):
        self.event_log: D4PyEventLog = event_log

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

        return pm4py.filter_time_range(self.event_log.log, start_date, end_date, mode, timestamp_key, case_id_key)

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
        return pm4py.filter_case_performance(self.event_log.log, min_performance, max_performance, timestamp_key,
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
        return pm4py.get_start_activities(self.event_log.log, activity_key, timestamp_key, case_id_key)

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
        return pm4py.filter_start_activities(self.event_log.log, activities, retain, activity_key, timestamp_key,
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
        return pm4py.get_end_activities(self.event_log.log, activity_key, timestamp_key, case_id_key)

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
        return pm4py.filter_end_activities(self.event_log.log, activities, retain, activity_key, timestamp_key,
                                           case_id_key)

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
        return pm4py.get_variants(self.event_log.log, activity_key, timestamp_key, case_id_key)

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
        return pm4py.filter_variants_top_k(self.event_log.log, k, activity_key, timestamp_key, case_id_key)

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
        return pm4py.filter_variants(self.event_log.log, variants, retain, activity_key, timestamp_key, case_id_key)

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

        return pm4py.get_event_attribute_values(self.event_log.log, attribute, count_once_per_case, case_id_key)

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

        return pm4py.filter_event_attribute_values(self.event_log.log, attribute_key, values, level, retain, case_id_key)
