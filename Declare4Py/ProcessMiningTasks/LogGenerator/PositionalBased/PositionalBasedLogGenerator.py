import typing
import logging
import os
import clingo
import warnings
from random import randrange

from Declare4Py.ProcessMiningTasks.AbstractLogGenerator import AbstractLogGenerator
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedModel import PositionalBasedModel


class PositionalBasedLogGenerator(AbstractLogGenerator):

    def __init__(self, total_traces: int, min_events: int, max_events: int, pb_model: PositionalBasedModel, verbose: bool = False):
        super().__init__(total_traces, min_events, max_events, pb_model, None, verbose)

        self.__PB_Logger = logging.getLogger("Positional Based Log Generator")

        self.use_custom_clingo_config: bool = False
        self.clingo_commands: typing.Dict[str, str] = {"CONFIG": "--configuration={}", "THREADS": "-t {}", "FREQUENCY": "--rand-freq={}", "SIGN-DEF": "--sign-def={}", "MODE": "--opt-mode={}", "STRATEGY": "--opt-strategy={}", "HEURISTIC": "--heuristic={}"}
        self.default_configuration: typing.Dict[str, str] = {"CONFIG": "trendy", "THREADS": str(os.cpu_count()), "FREQUENCY": "0.3", "SIGN-DEF": "asp", "MODE": "optN", "STRATEGY": None, "HEURISTIC": None}
        self.custom_configuration: typing.Dict[str, str] = self.default_configuration.copy()

        self.pb_model: PositionalBasedModel = pb_model

        self.__generate_positives: bool = True
        self.positive_results: typing.List = []
        self.negatives_results: typing.List = []

    def run(self, generate_negatives_traces: bool = False, noise_percentage: int = 0, append_results: bool = False):

        if not append_results:
            self.positive_results = []
            self.negatives_results = []

        noise_percentage = 0 if noise_percentage < 0 else noise_percentage
        noise_percentage = 100 if noise_percentage > 100 else noise_percentage

        clingo_configuration: typing.List[str] = self.__prepare_clingo_configuration()

        self.__generate_positives = True
        self.__run_clingo_per_trace_set(self.pb_model.to_asp(True), clingo_configuration)

        if generate_negatives_traces:
            self.__generate_positives = False
            self.__run_clingo_per_trace_set(self.pb_model.to_asp(True, True), clingo_configuration, "Negatives")

        print("Positives: ")
        print(self.positive_results)
        print("Negatives: ")
        print(self.negatives_results)

    def __run_clingo_per_trace_set(self, asp: str, clingo_configuration: typing.List[str], trace_type: str = "Positives"):

        for num_events, num_traces in self.compute_distribution().items():

            # Defines some important parameters for clingo
            arguments: typing.List = [
                "-c",
                f"p={int(num_events)}",
                f"{int(num_traces)}",
                f"--seed={randrange(0, 2 ** 30 - 1)}",
                "--project",
                "--restart-on-model",
            ]

            # Appends the options of our configurations
            arguments += clingo_configuration

            # Sets up clingo
            ctl = clingo.Control(arguments)
            ctl.add(asp)
            ctl.ground([("base", [])], context=self)

            self.__debug_message(f"Total traces to generate and events: Traces:{num_traces}, Events: {num_events}")

            res = ctl.solve(on_model=self.__handle_clingo_result)
            self.__debug_message(f"Clingo Result :{str(res)}")

            if res.unsatisfiable:
                warnings.warn(f'WARNING: Cannot generate {num_traces} {trace_type} trace/s exactly with {num_events} events with this Declare model. Check the definition of your constraints')


    def __handle_clingo_result(self, output: clingo.solving.Model):
        """A callback method which is given to the clingo """
        symbols = output.symbols(shown=True)
        self.__debug_message(f" Traces generated :{symbols}")
        if self.__generate_positives:
            self.positive_results.append(symbols)
        else:
            self.negatives_results.append(symbols)


    def __prepare_clingo_configuration(self) -> typing.List[str]:

        if self.use_custom_clingo_config:
            config = self.custom_configuration
        else:
            config = self.default_configuration

        # Creating appendable configuration to the clingo controller
        # Based on the current clingo configuration used by the generator
        configuration: typing.List = []

        for key, value in config.items():
            if value is not None:
                configuration.append(self.clingo_commands[key].format(value))

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

        self.use_custom_clingo_config = True
        if config is not None:
            self.custom_configuration["CONFIG"] = str(config)
        if threads is not None:
            self.custom_configuration["THREADS"] = str(abs(threads))
        else:
            self.custom_configuration["THREADS"] = str(os.cpu_count())
        if frequency is not None:
            self.custom_configuration["FREQUENCY"] = str(frequency)
        if sign_def is not None:
            self.custom_configuration["SIGN-DEF"] = str(sign_def)
        if mode is not None:
            self.custom_configuration["MODE"] = str(mode)
        if strategy is not None:
            self.custom_configuration["STRATEGY"] = str(strategy)
        if heuristic is not None:
            self.custom_configuration["HEURISTIC"] = str(heuristic)

    def use_default_clingo_configuration(self):
        """
        Enables the use of default clingo configuration.
        """

        self.use_custom_clingo_config = False

    def get_current_clingo_configuration(self) -> typing.Dict[str, str]:
        """
        Returns the current clingo configuration.
        It returns the default clingo configuration if the variable use_default_clingo_configuration is False.
        It returns the custom clingo configuration if the variable use_default_clingo_configuration is True.
        """

        if self.use_custom_clingo_config:
            return self.custom_configuration
        else:
            return self.default_configuration

    def set_positional_based_model(self, pb_model: PositionalBasedModel):
        self.pb_model = pb_model

    def get_positional_based_model(self) -> PositionalBasedModel:
        return self.pb_model

    def __debug_message(self, msg: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """

        if self.verbose:
            self.__PB_Logger.debug(str(msg))

if __name__ == '__main__':

    path = "Declare_Tests/"
    no_constraints = "NO_CONSTRAINTS"
    model_name = path + no_constraints

    model1 = PositionalBasedModel(True).parse_from_file(f"{model_name}.decl")
    model1.to_asp_file(f"{model_name}.lp")
    generator = PositionalBasedLogGenerator(3, 20,20, model1, True)
    generator.run()
