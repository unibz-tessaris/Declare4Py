import pdb
from abc import ABC

from logaut import ltl2dfa

from src.Declare4Py.ProcessModels.AbstractModel import ProcessModel
from pylogics.parsers import parse_ltl
from src.Declare4Py.Utils.utils import Utils
from typing import List


class LTLModel(ProcessModel, ABC):

    def __init__(self, backend: str = "lydia"):
        super().__init__()
        self.formula: str = ""
        self.parsed_formula = None
        self.parameters = []
        self.backend = backend

    def get_backend(self) -> str:
        """
        Returns the current backend used to translate an LTLf formula into a DFA.

        Returns:
            str: the current backend

        """
        return self.backend

    def to_lydia_backend(self) -> None:
        """
        Switch to lydia backend

        """
        self.backend = "lydia"

    def to_ltlf2dfa_backend(self) -> None:
        """
        Switch to ltlf2dfa backend

        """
        self.backend = "ltlf2dfa"

    def add_conjunction(self, new_formula: str) -> None:
        """
        This method puts in conjunction the LTLf formula of the class with the input LTLf formula

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) && ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_disjunction(self, new_formula: str) -> None:
        """
        This method puts in disjunction the LTLf formula of the class with the input LTLf formula

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) || ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_implication(self, new_formula: str) -> None:
        """
        This method add on implication between the LTLf formula of the class (left part) with the input LTLf formula
        (left part)

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) -> ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_equivalence(self, new_formula: str) -> None:
        """
        This method add o biimplication between the LTLf formula of the class (left part) with the input LTLf formula
        (left part)

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) <-> ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_negation(self) -> None:
        """
        This method negates the the LTLf formula of the class

        """
        self.formula = f"!({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_next(self) -> None:
        """
        This method adds the next operator in front of the LTLf formula of the class

        """
        self.formula = f"X({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_eventually(self) -> None:
        """
        This method adds the eventually operator in front of the LTLf formula of the class

        """
        self.formula = f"F({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_always(self) -> None:
        """
        This method adds the always operator in front of the LTLf formula of the class

        """
        self.formula = f"G({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_until(self, new_formula: str) -> None:
        """

        Args:
            new_formula:

        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) U ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def check_satisfiability(self, minimize_automaton: bool = True) -> bool:
        """

        Args:
            minimize_automaton:

        Returns:
            bool:

        """
        if self.parsed_formula is None:
            raise RuntimeError("You must load the LTL model before checking the model.")
        if self.backend not in ["lydia", "ltlf2dfa"]:
            raise RuntimeError("Only lydia and ltlf2dfa are supported backends.")
        dfa = ltl2dfa(self.parsed_formula, backend=self.backend)
        if minimize_automaton:
            dfa = dfa.minimize()
        if len(dfa.accepting_states) > 0:
            return True
        else:
            return False

    def parse_from_string(self, content: str, new_line_ctrl: str = "\n") -> None:
        """
        This function expects an LTL formula as a string.
        The pylogics library is used, reference to it in case of doubt.
        Refer to http://ltlf2dfa.diag.uniroma1.it/ltlf_syntax
        for allowed LTL symbols.
        We allow unary operators only if followed by parenthesis, e.g.: G(a), X(a), etc..

        Args:
            content: string containing the LTL formula to be passed

        Returns:
            Void

        """
        if type(content) is not str:
            raise RuntimeError("You must specify a string as input formula.")

        formula = Utils.normalize_formula(content)
        try:
            self.parsed_formula = parse_ltl(formula)
        except RuntimeError:
            raise RuntimeError(f"The inserted string: \"{formula}\" is not a valid LTL formula")

        self.formula = formula


class LTLTemplate:
    """
    Class that allows the user to create a template. User can choose between various standard formulae.
    Makes use of the class LTLModel.
    Insert a string representing one of the seven available template functions
    """

    def __init__(self, template_str: str):
        self.template_str: str = template_str
        self.parameters: [str] = []
        self.ltl_templates = {'eventually_a': self.eventually_a,
                              'eventually_a_then_b': self.eventually_a_then_b,
                              'eventually_a_or_b': self.eventually_a_or_b,
                              'eventually_a_next_b': self.eventually_a_next_b,
                              'eventually_a_then_b_then_c': self.eventually_a_then_b_then_c,
                              'eventually_a_next_b_next_c': self.eventually_a_next_b_next_c,
                              'next_a': self.next_a}

        self.tb_declare_templates = {'responded_existence': self.responded_existence,
                                     'response': self.response,
                                     'alternate_response': self.alternate_response,
                                     'chain_response': self.chain_response,
                                     'precedence': self.precedence,
                                     'alternate_precedence': self.alternate_precedence,
                                     'chain_precedence': self.chain_precedence,
                                     'not_responded_existence': self.not_responded_existence,
                                     'not_response': self.not_response,
                                     'not_precedence': self.not_precedence,
                                     'not_chain_response': self.not_chain_response,
                                     'not_chain_precedence': self.not_chain_precedence}

        self.templates = {**self.ltl_templates, **self.tb_declare_templates}

        if template_str in self.templates:
            self.template_str = template_str
        else:
            raise RuntimeError(f"{template_str} is a not a valid template. Check the tutorial here "
                               f"https://declare4py.readthedocs.io/en/latest/tutorials/2.Conformance_checking_LTL.html "
                               f"for a list of the valid templates")

    def get_ltl_templates(self) -> List[str]:
        return [template for template in self.ltl_templates]

    def get_tb_declare_templates(self) -> List[str]:
        return [template for template in self.tb_declare_templates]

    @staticmethod
    def eventually_a(activity: List[str]) -> str:
        formula_str = "F(" + activity[0] + ")"
        return formula_str

    @staticmethod
    def eventually_a_then_b(activity: List[str]) -> str:
        formula_str = "F(" + activity[0] + " && F(" + activity[1] + "))"
        return formula_str

    @staticmethod
    def eventually_a_or_b(activity: List[str]) -> str:
        formula_str = "F(" + activity[0] + ") || F(" + activity[1] + ")"
        return formula_str

    @staticmethod
    def eventually_a_next_b(activity: List[str]) -> str:
        formula_str = "F(" + activity[0] + " && X(" + activity[1] + "))"
        return formula_str

    @staticmethod
    def eventually_a_then_b_then_c(activity: List[str]) -> str:
        formula_str = "F(" + activity[0] + " && F(" + activity[1] + " && F(" + activity[2] + ")))"
        return formula_str

    @staticmethod
    def eventually_a_next_b_next_c(activity: List[str]) -> str:
        formula_str = "F(" + activity[0] + " && X(" + activity[1] + " && X(" + activity[2] + ")))"
        return formula_str

    @staticmethod
    def next_a(act: [str]) -> str:
        formula_str = "X(" + act[0] + ")"
        return formula_str

    # Branched Declare Models
    @staticmethod
    def responded_existence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "F(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ") -> F(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ")"
        return formula

    @staticmethod
    def response(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "G((" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ") -> F(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))"
        return formula

    @staticmethod
    def alternate_response(activities_a: List[str], activities_b: List[str]) -> str:
        """
        This function fills the alternate response template with the ORs of two sets of activities.

        Args:
            activities_a: the list of activation activities
            activities_b: the list of target activities

        Returns:
            str: a string formula filled with the sets of activities

        """
        formula = "G((" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ") -> X((!(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ")U( " + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))))"
        return formula

    @staticmethod
    def chain_response(activities_a: List[str], activities_b: List[str]) -> str:
        """
        This function fills the chain response template with the ORs of two sets of activities.

        Args:
            activities_a: the list of activation activities
            activities_b: the list of target activities

        Returns:
            str: a string formula filled with the sets of activities

        """
        formula = "G((" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += "  || " + activities_a[i]
        formula += ") -> X(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))"
        return formula

    @staticmethod
    def precedence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "((!(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))U(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ")) || G(!(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]

        formula += "))"
        return formula

    @staticmethod
    def alternate_precedence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "((!(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))U(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ")) && G((" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ") -> X((!(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))U(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ")) || G(!(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ")))"
        return formula

    @staticmethod
    def chain_precedence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "G(X(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ") -> " + "(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += "))"
        return formula

    @staticmethod
    def not_responded_existence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "F(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ") -> !(F(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += "))"
        return formula

    @staticmethod
    def not_response(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "G((" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ") -> !(F(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ")))"
        return formula

    @staticmethod
    def not_precedence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "G(F(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ") ->!(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += "))"
        return formula

    @staticmethod
    def not_chain_response(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "G((" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + activities_a[i]
        formula += ") -> X(!(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ")))"
        return formula

    @staticmethod
    def not_chain_precedence(activities_a: List[str], activities_b: List[str]) -> str:
        formula = "G( X(" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + activities_b[i]
        formula += ") -> !(" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || "+activities_a[i]
        formula += "))"
        return formula

    def fill_template(self, *activities: List[str]) -> LTLModel:
        """
        This function fills the template with the input lists of activities and returns an LTLModel object containing
        the filled LTLf formula of the template

        Args:
            *activities: list of activities to pass to the template function

        Returns:
            LTLModel: LTLf Model of the filled formula of the template

        """
        if self.template_str is None:
            raise RuntimeError("Please first load a valid template")
        func = self.templates.get(self.template_str)
        filled_model = LTLModel()
        try:
            formula = func(*activities)
            for act in activities:
                act = [item.lower() for item in act]
                act = [Utils.parse_activity(item) for item in act]
                self.parameters += act
            filled_model.parse_from_string(formula)
            filled_model.parameters = self.parameters
        except (TypeError, RuntimeError):
            raise TypeError("Mismatched number of parameters or type")
        return filled_model
