import logging
import os
import typing
import warnings
import math
from datetime import datetime, timedelta
from random import randrange

import clingo
import pandas as pd

from Declare4Py.ProcessMiningTasks.AbstractLogGenerator import AbstractLogGenerator
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedModel import PositionalBasedModel
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.ASPUtils import ASPFunctions
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.PBEncoder import Encoder


class PositionalBasedLogGenerator(AbstractLogGenerator):

    def __init__(self, total_traces: int, min_events: int, max_events: int, pb_model: PositionalBasedModel, verbose: bool = False):
        super().__init__(total_traces, min_events, max_events, pb_model, None, verbose)

        self.__PB_Logger = logging.getLogger("Positional Based Log Generator")

        self.__use_custom_clingo_config: bool = False
        self.__clingo_commands: typing.Dict[str, str] = {"CONFIG": "--configuration={}", "THREADS": "--parallel-mode={},split", "FREQUENCY": "--rand-freq={}", "SIGN-DEF": "--sign-def={}",
                                                         "MODE": "--opt-mode={}", "STRATEGY": "--opt-strategy={}", "HEURISTIC": "--heuristic={}"}
        self.__default_configuration: typing.Dict[str, str] = {"CONFIG": "tweety", "TIME-LIMIT": "120", "THREADS": str(os.cpu_count()), "FREQUENCY": "0.9", "SIGN-DEF": "rnd", "MODE": "optN",
                                                               "STRATEGY": None, "HEURISTIC": None}
        self.__custom_configuration: typing.Dict[str, str] = self.__default_configuration.copy()

        self.__pb_model: PositionalBasedModel = pb_model

        self.__generate_positives: bool = True
        self.__positive_results: typing.Dict = {}
        self.__negatives_results: typing.Dict = {}
        self.__current_asp_rule: str = ""

        self.__pd_cols: typing.List[str] = ["case:concept:name", "time:timestamp", "concept:name:order", "concept:name:rule", "concept:name:time", "concept:name", "case:label"] + list(
            pb_model.get_attributes_dict().keys())
        self.__new_pd_row: typing.Dict[str, typing.Any] = dict(zip(self.__pd_cols, [None for _ in range(len(self.__pd_cols))]))
        self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)

    def run(self, generate_negatives_traces: bool = False, append_results: bool = False):

        if not append_results:
            self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)

        self.__positive_results = {}
        self.__negatives_results = {}

        clingo_configuration: typing.List[str] = self.__prepare_clingo_configuration()

        self.__generate_positives = True
        self.__run_clingo_per_trace_set(self.__pb_model.to_asp_with_single_constraints(True), clingo_configuration)
        self.__parse_results(self.__positive_results, "Positive")

        if generate_negatives_traces:
            self.__generate_positives = False
            self.__run_clingo_per_trace_set(self.__pb_model.to_asp_with_single_constraints(True, True), clingo_configuration, "Negatives")
            self.__parse_results(self.__negatives_results, "Negative")

    def __run_clingo_per_trace_set(self, asp_list: typing.List[str], clingo_configuration: typing.List[str], trace_type: str = "Positives"):

        for index, asp in enumerate(asp_list):

            if trace_type == "Positives":
                self.__current_asp_rule = "Rule_" + str(index + 1)
            else:
                self.__current_asp_rule = "Not_Rule_" + str(index + 1)

            for num_events, num_traces in self.compute_distribution(math.ceil(self.log_length / len(asp_list))).items():

                # Defines some important parameters for clingo
                arguments: typing.List = [
                    "-c",
                    f"p={int(num_events)}",
                    f"{int(num_traces)}",
                    f"--seed={randrange(0, 2 ** 30 - 1)}",
                    "--share=auto",
                    "--distribute=conflict,global,4",
                    "--integrate=gp",
                    "--enum-mode=auto",
                    "--deletion=basic,75,activity",
                    "--del-init=3.0",
                    "--shuffle=1",
                    "--project",
                ]

                # Appends the options of our configurations
                arguments += clingo_configuration

                # Sets up clingo
                ctl = clingo.Control(arguments)
                ctl.add(asp)
                ctl.ground([("base", [])], context=self)

                self.__debug_message(f"Total traces to generate and events: Traces:{num_traces}, Events: {num_events}")

                with ctl.solve(on_model=self.__handle_clingo_result, async_=True) as handle:
                    handle.wait(self.__get_clingo_time_limit())
                    handle.cancel()
                    res = handle.get()

                self.__debug_message(f"Clingo Result :{str(res)}")

                if res.unsatisfiable:
                    warnings.warn(f'WARNING: Cannot generate {num_traces} {trace_type} trace/s exactly with {num_events} events with this Declare model model rule {self.__current_asp_rule}. Check the definition of your constraints')

    def __parse_results(self, results: typing.Dict, label: str):

        if results is None or len(results) == 0:
            return

        for rule, results in results.items():
            for trace_index, trace in enumerate(results):

                events: typing.List[typing.Any] = []
                values: typing.List[typing.Any] = []

                for function in trace:
                    if function.name == ASPFunctions.ASP_TIMED_EVENT_NAME:

                        activity = Encoder().decode_value(function.arguments[0].name)
                        pos = function.arguments[1].number
                        time = function.arguments[2].number

                        events.append([activity, pos, time])

                    elif function.name == ASPFunctions.ASP_ASSIGNED_VALUE_NAME:

                        attribute = Encoder().decode_value(function.arguments[0].name)
                        try:
                            value = Encoder().decode_value(function.arguments[1].name)
                        except RuntimeError:
                            value = self.__pb_model.apply_precision(attribute, function.arguments[1].number)
                        pos = function.arguments[2].number

                        values.append([attribute, value, pos])
                    else:
                        self.__debug_message(f"Couldn't parse clingo function {function}")

                events.sort(key=lambda x: int(x[1]))

                # Randomized start by one hour
                delta = timedelta(seconds=randrange(0, 3600))

                for activity, pos, time in events:
                    new_row: typing.Dict[str, typing.Any] = self.__new_pd_row.copy()
                    new_row["case:concept:name"] = "case_" + str(trace_index)
                    new_row["concept:name:order"] = "event_" + str(pos)
                    new_row["time:timestamp"] = datetime.now() + delta + timedelta(seconds=time * self.__pb_model.get_time_unit_in_seconds())
                    new_row["concept:name:rule"] = str(rule)
                    new_row["concept:name:time"] = "time_" + str(time)
                    new_row["concept:name"] = activity
                    new_row["case:label"] = label

                    for attribute, value, _ in filter(lambda x: pos == int(x[2]), values):
                        new_row[attribute] = value
                    self.__pd_results = pd.concat([self.__pd_results, pd.DataFrame([new_row])], ignore_index=True)

    def to_csv(self, csv_path: str):
        self.__pd_results.to_csv(csv_path)

    def __handle_clingo_result(self, output: clingo.solving.Model):
        """A callback method which is given to the clingo """
        symbols = output.symbols(shown=True)
        self.__debug_message(f" Traces generated :{symbols}")
        if self.__generate_positives:
            if self.__current_asp_rule not in self.__positive_results.keys():
                self.__positive_results[self.__current_asp_rule] = []
            self.__positive_results[self.__current_asp_rule].append(symbols)
        else:
            if self.__current_asp_rule not in self.__negatives_results.keys():
                self.__negatives_results[self.__current_asp_rule] = []
            self.__negatives_results[self.__current_asp_rule].append(symbols)

    def __prepare_clingo_configuration(self) -> typing.List[str]:

        if self.__use_custom_clingo_config:
            config = self.__custom_configuration
        else:
            config = self.__default_configuration

        # Creating appendable configuration to the clingo controller
        # Based on the current clingo configuration used by the generator
        configuration: typing.List = []

        for key, value in config.items():
            if value is not None and key in self.__clingo_commands.keys():
                configuration.append(self.__clingo_commands[key].format(value))

        return configuration

    def __get_clingo_time_limit(self) -> int:
        if self.__use_custom_clingo_config:
            return int(self.__custom_configuration["TIME-LIMIT"])
        return int(self.__default_configuration["TIME-LIMIT"])

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
        self.__pb_model = pb_model
        self.__pd_cols: typing.List[str] = ["case:concept:name", "time:timestamp", "concept:name:order", "concept:name", "case:label"] + list(pb_model.get_attributes_dict().keys())
        self.__new_pd_row: typing.Dict[str, typing.Any] = dict(zip(self.__pd_cols, [None for _ in range(len(self.__pd_cols))]))
        self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)

    def get_positional_based_model(self) -> PositionalBasedModel:
        return self.__pb_model

    def __debug_message(self, msg: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """

        if self.verbose:
            self.__PB_Logger.debug(str(msg))


if __name__ == '__main__':
    path = "Declare_Tests/"
    no_constraints = "NO_CONSTRAINTS"
    model1 = "model"
    model_name = path + model1

    model1 = PositionalBasedModel(verbose=True).parse_from_file(f"{model_name}.decl")
    # model1.to_asp_file(f"{model_name}.lp", True)
    generator = PositionalBasedLogGenerator(20, 10, 10, model1, True)
    generator.run()
    generator.to_csv(model_name + ".csv")
