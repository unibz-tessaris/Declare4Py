import logging
import os
import random
import typing
import warnings
import math
from datetime import datetime, timedelta
from random import randrange

import clingo
import pm4py
from clingo.script import register_script
import pandas as pd

from Declare4Py.ProcessMiningTasks.AbstractLogGenerator import AbstractLogGenerator
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedModel import PositionalBasedModel
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.ASPUtils import ASPFunctions, ASPClingoScript
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.PBEncoder import Encoder


class PositionalBasedLogGenerator(AbstractLogGenerator):
    """
    The Positional Based Log Generator represents the class that generates positional based logs given a positional based model
    """

    # Constructor
    def __init__(self, total_traces: int, min_events: int, max_events: int, pb_model: PositionalBasedModel, verbose: bool = False):
        # Initializes the superclass
        super().__init__(total_traces, min_events, max_events, pb_model, None, verbose)

        # Initializes the logger
        self.__PB_Logger = logging.getLogger("Positional Based Log Generator")

        # Initializes clingo configuration information
        self.__use_custom_clingo_config: bool = False
        self.__clingo_commands: typing.Dict[str, str] = {"CONFIG": "--configuration={}", "THREADS": "--parallel-mode={},compete", "FREQUENCY": "--rand-freq={}", "SIGN-DEF": "--sign-def={}",
                                                         "MODE": "--opt-mode={}", "STRATEGY": "--opt-strategy={}", "HEURISTIC": "--heuristic={}"}
        self.__default_configuration: typing.Dict[str, str] = {"CONFIG": "jumpy", "TIME-LIMIT": "120", "THREADS": str(os.cpu_count()), "FREQUENCY": "1", "SIGN-DEF": "rnd", "MODE": "optN",
                                                               "STRATEGY": "bb", "HEURISTIC": "Vsids"}
        self.__custom_configuration: typing.Dict[str, str] = self.__default_configuration.copy()

        # sets the positional based model
        self.__pb_model: PositionalBasedModel = pb_model

        # Initializes the results dictionaries and correlated information
        self.__generate_positives: bool = True
        self.__positive_results: typing.Dict = {}
        self.__negatives_results: typing.Dict = {}
        self.__current_asp_rule: str = ""

        # Initializes the pandas dataframe with the results
        self.__pd_cols: typing.List[str] = ["case:concept:name", "time:timestamp", "concept:name:order", "concept:name:rule", "concept:name:time", "concept:name", "case:label"] + list(
            pb_model.get_attributes_dict().keys())
        self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)
        # Counts the number of traces currently in the dataframe
        self.__case_index: int = 0

        # Registers the script for solving range problems to the clingo library in order to use the function during the runtime of clingo
        register_script(ASPFunctions.ASP_PYTHON_SCRIPT_NAME, ASPClingoScript())

    def run(self, equal_rule_split: bool = True, high_variability: bool = True, generate_negatives_traces: bool = False, positive_noise_percentage: int = 0, negative_noise_percentage: int = 0, append_results: bool = False):
        """
        Method that generates positional based logs:

        Parameters
            equal_rule_split: bool = If True the generation will not be random and each rule will appear in a uniform manner
            high_variability: bool = If True Generates the traces singularly otherwise generates the traces together with low variability
            generate_negatives_traces: bool = If True generates also the negative logs
            append_results: bool = If True appends the new log results to the existing logs
            positive_noise_percentage: int = Indicates the noise in the positive traces
            negative_noise_percentage: int = Indicates the noise in the negative traces
        """

        # Checks if the result must be appended, otherwise resets the dataframe
        if not append_results:
            self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)
            self.__case_index: int = 0

        # Resets the results dicts
        self.__positive_results = {}
        self.__negatives_results = {}

        # Prepares the clingo configuration
        clingo_configuration: typing.List[str] = self.__prepare_clingo_configuration()

        # Sets the current generation logs
        self.__generate_positives = True

        # Prepares from the model the ASP model
        asp, equal_rule_split = self.__prepare_asp_models(equal_rule_split)

        # Runs clingo and parses the results for the positive traces
        self.__run_clingo_per_trace_set(asp, clingo_configuration, equal_rule_split, high_variability, "Positives")
        self.__parse_results(self.__positive_results, "Positive", positive_noise_percentage)

        # If the generator must solve also the negative traces
        if generate_negatives_traces:
            # Sets the current generation logs
            self.__generate_positives = False

            # Prepares from the model the ASP model
            asp, equal_rule_split = self.__prepare_asp_models(equal_rule_split, True)

            # Runs clingo and parses the results for the negative traces
            self.__run_clingo_per_trace_set(asp, clingo_configuration, equal_rule_split, high_variability, "Negatives")
            self.__parse_results(self.__negatives_results, "Negative", negative_noise_percentage)

    def __prepare_asp_models(self, equal_rule_split: bool, generate_negatives: bool = False):
        """
        Prepares the list of models for the generation
        """
        # Prepares the normal model
        asp = [self.__pb_model.to_asp(encode=True)]

        # If the user wants a uniform generation
        if equal_rule_split:
            # Generates the asp model for each constraint
            asp_models = self.__pb_model.to_asp_with_single_constraints(encode=True, generate_negatives=generate_negatives)
            # If the asp model doesn't have constraints use the normal model
            # Otherwise replace the normal model with the list of models with 1 constraint each
            if len(asp_models) == 0:
                equal_rule_split = False
            else:
                asp = asp_models

        # Return the models and the equal split rule for the solver
        return asp, equal_rule_split

    def __run_clingo_per_trace_set(self, asp_list: typing.List[str], clingo_configuration: typing.List[str], equal_rule_split: bool, high_variability: bool = True, trace_type: str = "Positives"):
        """
        Runs clingo for each set traces
        """

        # For every asp model
        for index, asp in enumerate(asp_list):

            # Set the current ASP rule
            if trace_type == "Positives":
                self.__current_asp_rule = "Rule_"
            else:
                self.__current_asp_rule = "Not_Rule_"
            # Set the current ASP rule
            if equal_rule_split:
                self.__current_asp_rule += str(index + 1)
            else:
                self.__current_asp_rule += "?"

            # For every number of events in the numer of traces generates a uniform set of trace
            for num_events, num_traces in self.compute_distribution(math.ceil(self.log_length / len(asp_list))).items():

                if high_variability:
                    for num_trace in range(num_traces):
                        # Signals the user for the start of the process
                        self.__debug_message(f"Generating trace number {num_traces} with Events: {num_events}")
                        self.__run_clingo(asp, clingo_configuration, num_events, 1, num_trace, trace_type)
                else:
                    # Signals the user for the start of the process
                    self.__debug_message(f"Generating {num_traces} traces with Events: {num_events}")
                    self.__run_clingo(asp, clingo_configuration, num_events, num_traces, num_traces, trace_type)

    def __run_clingo(self, asp: str, clingo_configuration: typing.List[str], num_events: int, traces_to_generate: int, num_traces: int, trace_type: str = "Positives"):
        """
        Runs clingo for one or more traces
        """

        arguments: typing.List = [
            "-c",
            f"p={int(num_events)}",
            f"{traces_to_generate}",
            f"--seed={randrange(0, 2 ** 30 - 1)}",
            "--project"
        ]

        # Appends the options of our configurations
        arguments += clingo_configuration

        # Adds the arguments to clingo
        ctl = clingo.Control(arguments)
        ctl.add(asp)
        # Inserts the function for the range in clingo
        ctl.add('base', [], ASPFunctions.ASP_PYTHON_RANGE_SCRIPT)
        ctl.ground([('base', [])])

        # Not sure if it works as intended
        # Should stop the clingo after x seconds
        # Starts the solving process
        # res = ctl.solve(on_model=self.__handle_clingo_result)
        with ctl.solve(on_model=self.__handle_clingo_result, async_=True) as handle:
            handle.wait(self.__get_clingo_time_limit())
            handle.cancel()
            res = handle.get()

        # Print results
        self.__debug_message(f" Clingo Result :{str(res)}")
        # Raise a Warning if UNSAT
        if res.unsatisfiable:
            warnings.warn(
                f'WARNING: Cannot generate {num_traces} {trace_type} trace/s exactly with {num_events} events with this Declare model model rule {self.__current_asp_rule}. Check the definition of your constraints')

    def __parse_results(self, results: typing.Dict, label: str, noise_percentage: int = 0):

        """
        Parses the result generated by clingo
        """

        self.__debug_message(f"Starting parsing of {label} results")

        # If no results are found return
        if results is None or len(results) == 0:
            return

        # Prepare noise
        noise_percentage = self.__prepare_noise_percentage(noise_percentage)

        # Create a new entry for the pandas df
        new_df: typing.List = []

        # Initializes the minimum value of seconds and the maximum value of seconds to which 1 unit of Positional based time corresponds
        min_seconds, max_seconds = self.__pb_model.get_time_unit_in_seconds_range()

        # For each rule extract the results
        for rule, trace in results.items():

            # Stores all the formatted trace events after parsing
            formatted_traces: typing.List = []

            # Enumerate through the results
            for trace_index, trace_functions in enumerate(trace):
                # Initializes the events and values list
                self.__case_index += 1
                events: typing.List[typing.Any] = []
                values: typing.List[typing.Any] = []

                # For each function in the trace
                for function in trace_functions:

                    # If the function is "timed_event"
                    if function.name == ASPFunctions.ASP_TIMED_EVENT:
                        # Decode the activity
                        activity = Encoder().decode_value(function.arguments[0].name)
                        # Extract position and time
                        pos = function.arguments[1].number
                        time = function.arguments[2].number
                        # Save event
                        events.append([activity, pos, time])

                    # If the function is "assign_value"
                    elif function.name == ASPFunctions.ASP_ASSIGNED_VALUE:

                        # Decode the attribute
                        attribute = Encoder().decode_value(function.arguments[0].name)

                        # Try parsing the value of the attribute
                        try:
                            value = Encoder().decode_value(function.arguments[1].name)
                        except RuntimeError:
                            value = self.__pb_model.apply_precision(attribute, function.arguments[1].number)

                        # Parse the position
                        pos = function.arguments[2].number
                        # Save the attribute
                        values.append([attribute, value, pos])
                    else:
                        self.__debug_message(f"Couldn't parse clingo function {function}")

                # Sorts the events by position
                events.sort(key=lambda x: int(x[1]))

                # prepares a list of all the events in a trace
                trace_events: typing.List = []

                # Randomized start time by one hour
                time_delta: int = 0
                datetime_delta = datetime.now() + timedelta(seconds=randrange(0, 3599), milliseconds=randrange(0, 99999))

                # For each activity in the events
                for activity, pos, time in events:

                    # Calculates the time delta to add for the next event
                    time_delta = time - time_delta
                    datetime_delta += timedelta(seconds=sum([random.randint(min_seconds, max_seconds) for _ in range(time_delta)]))

                    # Initialize a new event
                    event: typing.Dict[str, typing.Any] = dict(zip(self.__pd_cols, [None for _ in range(len(self.__pd_cols))]))

                    # Initialize case information
                    event["case:concept:name"] = "case_" + str(self.__case_index)
                    event["concept:name:order"] = "event_" + str(pos)

                    # Assign and format the datetime of the event
                    event["time:timestamp"] = datetime_delta.strftime("%Y-%m-%d %H:%M:%S")

                    # Initialize case information
                    event["concept:name:rule"] = str(rule)
                    event["concept:name:time"] = "time_" + str(time)

                    # Initialize event information
                    event["concept:name"] = activity
                    event["case:label"] = label

                    # Assign each attribute where pos equals the position of the event to the new row
                    for attribute, value, _ in filter(lambda x: pos == int(x[2]), values):
                        event[attribute] = value

                    # Append the new event to the trace
                    trace_events.append(event)

                # Appends a formatted traces to the list of formatted traces
                formatted_traces.append(trace_events)

            # Apply noise
            if noise_percentage > 0:
                self.__debug_message(f"Applying noise percentage {noise_percentage} to the parsed results of rule: {str(rule)}")
                # Counts how many traces are formated
                traces_count = len(formatted_traces)

                # Creates an array of index to pick from in order to apply the noise
                # When an index is picked is then removed from the list, meaning that that index has already noise applied
                # Hence will not be selected during a later iteration for the application of the noise
                noise_index_list: typing.List[int] = [i for i in range(traces_count)]

                # For the number of traces to apply the noise
                for _ in range(math.ceil(traces_count / 100 * noise_percentage)):
                    # Extract a random index from the index list in range(0, len(noise_index_list) -1)
                    # Once extracted the len(noise_index_list) will diminish in size
                    trace_with_noise_index = noise_index_list.pop(random.randint(0, len(noise_index_list) - 1))

                    # Pop from the traces list the traces that hase noise
                    trace_with_noise = formatted_traces.pop(trace_with_noise_index)

                    # Apply the noise == label inversion to each event in the trace
                    for event in trace_with_noise:
                        event["case:label"] = "Positive" if event["case:label"] == "Negative" else "Negative"

                    # Reinsert the trace in the correct position
                    formatted_traces.insert(trace_with_noise_index, trace_with_noise)

            # Append to the new Dataframe the flattened list of lists: list of traces = [trace_1, ..., trace_n] and each trace_i = [event_1, ..., event_n]
            new_df += [events for trace in formatted_traces for events in trace]

        # Store the new results in the dataframe
        self.__pd_results = pd.concat([self.__pd_results, pd.DataFrame(new_df)], ignore_index=True)
        self.__debug_message(f"Completed parsing of {label} results")

    @staticmethod
    def __prepare_noise_percentage(noise_percentage: int = 0):
        """
        Fixes user input percentages
        """
        if not isinstance(noise_percentage, int) or noise_percentage < 0:
            noise_percentage = 0
        if noise_percentage > 100:
            noise_percentage = 100

        return noise_percentage

    def __handle_clingo_result(self, output: clingo.solving.Model):
        """
        A callback method which is given to the clingo
        """

        symbols = output.symbols(shown=True)
        self.__debug_message(f" Traces generated :{symbols}")
        # Checks if it is generating positive traces
        if self.__generate_positives:
            # Checks if the current rule is in the keys of the result dict. If not creates the entry
            if self.__current_asp_rule not in self.__positive_results.keys():
                self.__positive_results[self.__current_asp_rule] = []
            # Appends the result
            self.__positive_results[self.__current_asp_rule].append(symbols)

        # Otherwise is generating negatives
        else:
            # Checks if the current rule is in the keys of the result dict. If not creates the entry
            if self.__current_asp_rule not in self.__negatives_results.keys():
                self.__negatives_results[self.__current_asp_rule] = []
            # Appends the result
            self.__negatives_results[self.__current_asp_rule].append(symbols)

    def __prepare_clingo_configuration(self) -> typing.List[str]:
        """
        Prepares the clingo configuration
        """

        # Selects the correct configuration
        if self.__use_custom_clingo_config:
            config = self.__custom_configuration
        else:
            config = self.__default_configuration

        # Creating appendable configuration to the clingo controller
        # Based on the current clingo configuration used by the generator
        configuration: typing.List = []

        # Prepares the configuration
        for key, value in config.items():
            if value is not None and key in self.__clingo_commands.keys():
                configuration.append(self.__clingo_commands[key].format(value))

        # Returns the configuration
        return configuration

    def __get_clingo_time_limit(self) -> int:
        """
        Returns the clingo time limit for solving a problem
        """
        if self.__use_custom_clingo_config:
            return int(self.__custom_configuration["TIME-LIMIT"])
        return int(self.__default_configuration["TIME-LIMIT"])

    def to_csv(self, csv_path: str):
        """
        Export to csv file the current results
        """
        if not csv_path.endswith(".csv"):
            csv_path += ".csv"

        self.__pd_results.to_csv(csv_path)

    def to_xes(self, xes_path: str):
        """
        Export to xes file the current results
        """
        if not xes_path.endswith(".xes"):
            xes_path += ".xes"

        event_log = pm4py.format_dataframe(self.__pd_results, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
        pm4py.write_xes(event_log, xes_path)

    def use_custom_clingo_configuration(self,
                                        config: typing.Union[str, None] = None,
                                        time_limit: typing.Union[int, None] = None,
                                        threads: typing.Union[int, None] = None,
                                        frequency: typing.Union[float, int, None] = None,
                                        sign_def: typing.Union[str, None] = None,
                                        mode: typing.Union[str, None] = None,
                                        strategy: typing.Union[str, None] = None,
                                        heuristic: typing.Union[str, None] = None
                                        ):
        """
        Enables the use of custom clingo configuration.
        Changes the parameters of the custom configuration if the parameter is not None

        Parameters
            config:
                Clingo configuration
            time_limit:
                Maximum running time in seconds for clingo
            threads:
                Amount of Threads to be used
            frequency:
                Random frequency
            sign_def:
                Sign of the configuration
            mode:
                Optimization of the algorithm
            strategy:
                Optimization of the strategy
            heuristic:
                Used decision heuristic
        """

        self.__use_custom_clingo_config = True
        if config is not None:
            self.__custom_configuration["CONFIG"] = str(config)
        if time_limit is not None:
            self.__custom_configuration["TIME-LIMIT"] = str(int(time_limit))
        else:
            self.__custom_configuration["TIME-LIMIT"] = self.__default_configuration["TIME-LIMIT"]
        if threads is not None:
            self.__custom_configuration["THREADS"] = str(abs(threads))
        else:
            self.__custom_configuration["THREADS"] = self.__default_configuration["THREADS"]
        if frequency is not None:
            self.__custom_configuration["FREQUENCY"] = str(frequency)
        if sign_def is not None:
            self.__custom_configuration["SIGN-DEF"] = str(sign_def)
        if mode is not None:
            self.__custom_configuration["MODE"] = str(mode)
        if strategy is not None:
            self.__custom_configuration["STRATEGY"] = str(strategy)
        if heuristic is not None:
            self.__custom_configuration["HEURISTIC"] = str(heuristic)

    def use_default_clingo_configuration(self):
        """
        Enables the use of default clingo configuration.
        """

        self.__use_custom_clingo_config = False

    def reset_custom_clingo_configuration(self):
        """
        Resets the custom clingo configuration.
        """

        self.__custom_configuration = self.__default_configuration.copy()

    def get_current_clingo_configuration(self) -> typing.Dict[str, str]:
        """
        Returns the current clingo configuration.
        It returns the default clingo configuration if the variable use_default_clingo_configuration is False.
        It returns the custom clingo configuration if the variable use_default_clingo_configuration is True.
        """

        if self.__use_custom_clingo_config:
            return self.__custom_configuration
        else:
            return self.__default_configuration

    def set_positional_based_model(self, pb_model: PositionalBasedModel):
        """
        Changes the Positional Based Model
        """

        # Changes the model and some information needs to be recalculated
        self.__pb_model = pb_model
        self.__pd_cols: typing.List[str] = ["case:concept:name", "time:timestamp", "concept:name:order", "concept:name", "case:label"] + list(pb_model.get_attributes_dict().keys())
        self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)
        self.__case_index: int = 0

    def set_positional_based_time_range(self, positional_time_start: int = PositionalBasedModel.POSITIONAL_TIME_START, positional_time_end: int = PositionalBasedModel.POSITIONAL_TIME_END):
        """
        Sets the positional based time range of the model
        """
        self.__pb_model.set_positional_based_time_range(positional_time_start, positional_time_end)

    def set_time_unit_in_seconds_range(self, time_unit_in_seconds_min: int = PositionalBasedModel.TIME_UNIT_IN_SECONDS_RANGE_MIN, time_unit_in_seconds_max: int = PositionalBasedModel.TIME_UNIT_IN_SECONDS_RANGE_MAX):
        """
        Sets the time unit in seconds range of the model
        """
        self.__pb_model.set_positional_based_time_range(time_unit_in_seconds_min, time_unit_in_seconds_max)

    def get_time_unit_in_seconds_range(self) -> (int, int):
        """
        Returns the time unit in seconds conversion
        """
        return self.__pb_model.get_time_unit_in_seconds_range()

    def get_positional_based_model(self) -> PositionalBasedModel:
        """
        Returns the Positional Based Model
        """
        return self.__pb_model

    def get_results_as_dataframe(self) -> pd.DataFrame:
        """
        Returns the Result Dataframe
        """
        return self.__pd_results

    def __debug_message(self, msg: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """

        if self.verbose:
            self.__PB_Logger.debug(str(msg))


if __name__ == '__main__':
    model_name = "experimental_model"

    model1 = PositionalBasedModel(positional_time_end=20, verbose=True).parse_from_file(f"DeclareFiles/{model_name}.decl")
    model1.to_asp_file(f"ASPFiles/{model_name}.lp")
    model1.to_asp_file(f"ASPFiles/{model_name}_enc.lp", True)
    generator = PositionalBasedLogGenerator(50, 20, 20, model1, True)
    generator.run(generate_negatives_traces=True, positive_noise_percentage=10, negative_noise_percentage=10)
    generator.to_csv(f"LogResults/{model_name}.csv")
    generator.to_xes(f"LogResults/{model_name}.xes")
