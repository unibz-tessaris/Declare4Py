import logging
import os
import typing
import warnings
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
        self.__clingo_commands: typing.Dict[str, str] = {"CONFIG": "--configuration={}", "THREADS": "--parallel-mode {},split", "FREQUENCY": "--rand-freq={}", "SIGN-DEF": "--sign-def={}", "MODE": "--opt-mode={}", "STRATEGY": "--opt-strategy={}", "HEURISTIC": "--heuristic={}"}
        self.__default_configuration: typing.Dict[str, str] = {"CONFIG": "tweety", "THREADS": str(os.cpu_count()), "FREQUENCY": "0.9", "SIGN-DEF": "rnd", "MODE": "optN", "STRATEGY": None, "HEURISTIC": None}
        self.__custom_configuration: typing.Dict[str, str] = self.__default_configuration.copy()

        self.__pb_model: PositionalBasedModel = pb_model

        self.__generate_positives: bool = True
        self.__positive_results: typing.List = []
        self.__negatives_results: typing.List = []

        self.__pd_cols: typing.List[str] = ["case:concept:name", "time:timestamp", "concept:name:order", "concept:name", "case:label"] + list(pb_model.get_attributes_dict().keys())
        self.__new_pd_row: typing.Dict[str, typing.Any] = dict(zip(self.__pd_cols, [None for _ in range(len(self.__pd_cols))]))
        self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)

    def run(self, generate_negatives_traces: bool = False, append_results: bool = False):

        if not append_results:
            self.__pd_results: pd.DataFrame = pd.DataFrame(columns=self.__pd_cols)

        self.__positive_results = []
        self.__negatives_results = []

        clingo_configuration: typing.List[str] = self.__prepare_clingo_configuration()

        self.__generate_positives = True
        self.__run_clingo_per_trace_set(self.__pb_model.to_asp(True), clingo_configuration)
        self.__parse_results(self.__positive_results, "Positive")

        if generate_negatives_traces:
            self.__generate_positives = False
            self.__run_clingo_per_trace_set(self.__pb_model.to_asp(True, True), clingo_configuration, "Negatives")
            self.__parse_results(self.__negatives_results, "Negative")


    def __run_clingo_per_trace_set(self, asp: str, clingo_configuration: typing.List[str], trace_type: str = "Positives"):

        for num_events, num_traces in self.compute_distribution().items():

            # Defines some important parameters for clingo
            arguments: typing.List = [
                f"p={int(num_events)}",
                f"{int(num_traces)}",
                f"--seed={randrange(0, 2 ** 30 - 1)}"
            ]

            # Appends the options of our configurations
            # arguments += clingo_configuration

            # Sets up clingo
            ctl = clingo.Control(arguments)
            ctl.add(asp)
            ctl.ground([("base", [])], context=self)

            self.__debug_message(f"Total traces to generate and events: Traces:{num_traces}, Events: {num_events}")

            res = ctl.solve(on_model=self.__handle_clingo_result)
            self.__debug_message(f"Clingo Result :{str(res)}")

            if res.unsatisfiable:
                warnings.warn(f'WARNING: Cannot generate {num_traces} {trace_type} trace/s exactly with {num_events} events with this Declare model. Check the definition of your constraints')

    def __parse_results(self, results: typing.List, label: str):

        if results is None or len(results) == 0:
            return

        for trace_index, trace in enumerate(results):

            events: typing.List[typing.Any] = []
            values: typing.List[typing.Any] = []

            for function in trace:
                if function.name == ASPFunctions.ASP_EVENT["name"]:
                    activity = Encoder().decode_value("ACTIVITIES", function.arguments[0].name)
                    pos = function.arguments[1].number
                    events.append([activity, pos])
                elif function.name == ASPFunctions.ASP_ASSIGNED_VALUE["name"]:
                    attribute = Encoder().decode_value("ATTRIBUTES", function.arguments[0].name)
                    pos = function.arguments[1].number
                    try:
                        value = Encoder().decode_value("ATTR_VALUES", function.arguments[2].name)
                    except RuntimeError:
                        value = self.__pb_model.apply_precision(attribute, function.arguments[2].number)
                    values.append([attribute, pos, value])
                else:
                    self.__debug_message(f"Couldn't parse clingo function {function}")

            events.sort(key=lambda x: int(x[1]))
            values.sort(key=lambda x: int(x[1]))

            for activity, pos in events:
                new_row: typing.Dict[str, typing.Any] = self.__new_pd_row.copy()
                new_row["case:concept:name"] = "case_" + str(trace_index)
                new_row["concept:name:order"] = "event_" + str(pos)
                new_row["concept:name"] = activity
                new_row["case:label"] = label

                for attribute, _, value in filter(lambda x: pos == int(x[1]), values):
                    new_row[attribute] = value
                self.__pd_results = pd.concat([self.__pd_results, pd.DataFrame([new_row])], ignore_index=True)

    def to_csv(self, csv_path: str):
        self.__pd_results.to_csv(csv_path)

    def __handle_clingo_result(self, output: clingo.solving.Model):
        """A callback method which is given to the clingo """
        symbols = output.symbols(shown=True)
        self.__debug_message(f" Traces generated :{symbols}")
        if self.__generate_positives:
            self.__positive_results.append(symbols)
        else:
            self.__negatives_results.append(symbols)


    def __prepare_clingo_configuration(self) -> typing.List[str]:

        if self.__use_custom_clingo_config:
            config = self.__custom_configuration
        else:
            config = self.__default_configuration

        # Creating appendable configuration to the clingo controller
        # Based on the current clingo configuration used by the generator
        configuration: typing.List = []

        for key, value in config.items():
            if value is not None:
                configuration.append(self.__clingo_commands[key].format(value))

        return configuration

    def use_custom_clingo_configuration(self,
                                        config: typing.Union[str, None] = None,
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
        if threads is not None:
            self.__custom_configuration["THREADS"] = str(abs(threads))
        else:
            self.__custom_configuration["THREADS"] = str(os.cpu_count())
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

    model1 = PositionalBasedModel(True).parse_from_file(f"{model_name}.decl")
    model1.to_asp_file(f"{model_name}.lp", True)
    generator = PositionalBasedLogGenerator(100, 10, 10, model1, True)
    print("end")
    generator.run()
    generator.to_csv(model_name + ".csv")
