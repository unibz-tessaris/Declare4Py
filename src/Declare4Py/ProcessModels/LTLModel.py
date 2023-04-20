from abc import ABC

from src.Declare4Py.ProcessModels.AbstractModel import ProcessModel
from pylogics.parsers import parse_ltl
from src.Declare4Py.Utils.utils import Utils

class LTLModel(ProcessModel, ABC):

    def __init__(self):
        super().__init__()
        self.formula: str = ""
        self.parsed_formula = None
        self.parameters = []

    def parse_from_string(self, formula: str, new_line_ctrl: str = "\n") -> None:
        """
        This function expects an LTL formula as a string.
        The pylogics library is used, reference to it in case of doubt.
        Refer to https://marcofavorito.me/tl-grammars/v/7d9a17267fbf525d9a6a1beb92a46f05cf652db6/
        for allowed LTL symbols.
        We allow unary operators only if followed by parenthesis, e.g.: G(a), X(a), etc..


        Args:
            formula: string containing the LTL formula to be passed
            new_line_ctrl:

        Returns:
            Void

        """
        parsed = None
        if type(formula) is not str:
            raise RuntimeError("You must specify a string as input formula.")

        unary_operators = {"g(": "G(", "x(": "X(", "f(": "F(", "x[!](": "X[!]("}

        binary_operators = {" u ": " U ", "u(": "U(", " r ": " R ", "r(": "R(", " w ": " W ",
                            "w(": "W(", " m ": " M ", "m(": "M(", " v ": " V ", "v(": "V("}

        formula = Utils.parse_activity(formula)

        formula = formula.lower()

        for key, value in unary_operators.items():
            formula = formula.replace(key, value)

        for key, value in binary_operators.items():
            formula = formula.replace(key, value)

        try:
            parsed = parse_ltl(formula)
        except RuntimeError:
            raise RuntimeError(f"The inserted string: \"{formula}\" is not a valid LTL formula")

        self.formula = formula
        self.parsed_formula = parsed


class LTLModelTemplate:
    """
    Class that allows the user to create a template. User can choose between various standard formulae.
    Makes use of the class LTLModel.
    Insert a string representing one of the seven available template functions
    """

    # Set of basic LTL formulae for user
    def eventually_activity_a(activity: str) -> str:
        formula_str = "F(" + activity + ")"
        return formula_str

    def eventually_a_then_b(activity1: str, activity2: str) -> str:
        formula_str = "F(" + activity1 + " && F(" + activity2 + "))"
        return formula_str

    def eventually_a_or_b(activity1: str, activity2: str) -> str:
        formula_str = "F(" + activity1 + ") || F(" + activity2 + ")"
        return formula_str

    def eventually_a_next_b(activity1: str, activity2: str) -> str:
        formula_str = "F(" + activity1 + " && X(" + activity2 + "))"
        return formula_str

    def eventually_a_then_b_then_c(activity1: str, activity2: str, activity3: str) -> str:
        formula_str = "F(" + activity1 + " && F(" + activity2 + " && F(" + activity3 + ")))"
        return formula_str

    def eventually_a_next_b_next_c(activity1: str, activity2: str, activity3: str) -> str:
        formula_str = "F(" + activity1 + " && X(" + activity2 + " && X(" + activity3 + ")))"
        return formula_str

    def next_a(act: str) -> str:
        formula_str = "X(" + act + ")"
        return formula_str

    # Branched Declare Models

    def responded_existence(sour: [str], target:[str]) -> str:
        formula = "F(" + sour[0]
        for i in range(len(sour)):
            formula += "|| " + sour[i]
        formula += " -> F(" + target[0]
        for i in range(len(target)):
            formula += "||" + target[i]
        formula += "))"
        return formula


    def response(sour: [str], target:[str]) -> str:
        formula = "G(" + sour[0]
        for i in range(len(sour)):
            formula += "|| " + sour[i]
        formula += " -> F(" + target[0]
        for i in range(len(target)):
            formula += "||" + target[i]
        formula += "))"
        return formula

    def alternate_response(sour: [str], target:[str]) -> str:
        formula = "G(" + sour[0]
        for i in range(len(sour)):
            formula += "|| " + sour[i]
        formula += " -> X((!(" + sour[0] + ") "
        for i in range(len(sour)):
            formula += "|| !(" + sour[i] + ") "
        formula += ")U( " + target[0]
        for i in range(1, len(target)):
            formula += "||" + target[i]
        formula += ")))"
        return formula

    def chain_response(sour: [str], target:[str]) -> str:
        formula = "G(" + sour[0]
        for i in range(len(sour)):
            formula += "|| " + sour[i]
        formula += " -> X(" + target[0]
        for i in range(len(target)):
            formula += "||" + target[i]
        formula += "))"
        return formula

    def precedence(sour: [str], target:[str]) -> str:
        formula = "((!(" + target[0] + ")"
        for i in range(1, len(target)):
            formula += "|| !(" + target[i] + ")"
        formula += ")U(" + sour[0]

        for i in range(1, len(sour)):
            formula += "|| " + sour[i]

        formula += ")) || G((!(" + target[1] + ")"
        for i in range(1, len(target)):
            formula += "||!(" + target[i] + ")"

        formula += "))"
        return formula

    def alternate_precedence(sour: [str], target:[str]) -> str:
        formula = "("
        for i in range(1, len(target)-1):
            formula += "!(" + target[i] + ")||"
        formula += "!(" + target[len(target)-1] + ")U(" + sour[0]
        for i in range(1,len(sour)):
            formula += "|| " + sour[i]
        formula += ")) && G(" + target[0]
        for i in range(1, len(target)):
            formula += "||" + target[i]
        formula += " -> X(("
        for i in range(1, len(target)-1):
            formula += "!(" + target[i] + ")||"
        formula += "!(" + target[len(target)-1] + ")U(" + sour[0]
        for i in range(1, len(sour)):
            formula += "|| " + sour[i]
        formula += ")) && G( !(" + target[0] + ")"
        for i in range(1, len(target)):
            formula += "||!(" + target[i] + ")"
        formula += ")))"
        return formula

    def chain_precedence(sour: [str], target:[str]) -> str:
        formula = "G(X(" + target[0]
        for i in range(1, len(target)):
            formula += "||" + target[i]
        formula += ") -> " + "(" + sour[0]
        for i in range(1, len(sour)):
            formula += "||" + sour[i]
        formula += "))"
        return formula

    def not_responded_existence(sour: [str], target:[str]) -> str:
        formula = "F(" + sour[0]
        for i in range(1,len(sour)):
            formula += "||" + sour[i]
        formula += ") -> !(F(" + target[0] + ")"
        for i in range(1, len(target)):
            formula += "|| F(" + target[i] + ")"
        formula += ")"
        return formula

    def not_response(sour: [str], target:[str]) -> str:
        formula = "G(" + sour[0]
        for i in range(1,len(sour)):
            formula += "|| " + sour[i]
        formula += " -> !(F(" + target[0] + "))"
        for i in range(1, len(target)):
            formula += "||!(F(" + target[i] + "))"
        formula += ")"
        return formula

    def not_precedence(sour: [str], target:[str]) -> str:
        formula = "G(F(" + target[0] + ")"
        for i in range(1, len(target)):
            formula += "|| F(" + target[i] + ")"
        formula += "->!(" + sour[0]
        for i in range(1,len(sour)):
            formula += "||" + sour[i]
        formula += "))"
        return formula

    def not_chain_response(sour: [str], target:[str]) -> str:
        formula = "G(" + sour[0]
        for i in range(1,len(sour)):
            formula += "|| " + sour[i]
        formula += " -> X(!(" + target[0] + ")"
        for i in range(1, len(target)):
            formula += "||!(" + target[i] + ")"
        formula += "))"
        return formula

    def not_chain_precedence(sour: [str], target:[str]) -> str:
        formula = "G( X(" + target[0]
        for i in range(1, len(target)):
            formula += "||" + target[i]
        formula += ") -> !(" + sour[0] + ")"
        for i in range(1,len(sour)):
            formula += "|| !("+sour[i]+")"
        formula +=")"
        return formula

    templates = {'eventually_activity_a': eventually_activity_a, 'eventually_a_then_b': eventually_a_then_b,
                 'eventually_a_or_b': eventually_a_or_b, 'eventually_a_next_b': eventually_a_next_b,
                 'eventually_a_then_b_then_c': eventually_a_then_b_then_c,
                 'eventually_a_next_b_next_c': eventually_a_next_b_next_c, 'next_a': next_a,
                 'responded_existence':responded_existence, 'response':response, 'alternate_response':alternate_response,
                 'chain_response':chain_response, 'precedence':precedence, 'alternate_precedence':alternate_precedence,
                 'chain_precedence':chain_precedence, 'not_responded_existence':not_responded_existence,
                 'not_response':not_response, 'not_precedence':not_precedence, 'not_chain_response':not_chain_response,
                 'not_chain_precedence':not_chain_precedence}
    templ_str: str = None

    parameters: [str] = []

    def __init__(self, templ_str: str):
        if templ_str in self.templates:
            self.templ_str = templ_str
        else:
            raise RuntimeError("Inserted parameter is not of type string or is not a template")

    def get_templ_model(self, *activities: str) -> LTLModel:
        """
        Function used to retrieve the selected template and returns an LTLModel object containing such template

        Args:
            *activities: List of parameters to pass to the selected template function

        Returns:
            Model of the template formula

        """
        if self.templ_str is None:
            raise RuntimeError("Please first load a valid template")
        func = self.templates.get(self.templ_str)
        m = None
        try:
            formula = func(*activities)
            for act in activities:
                act = Utils.parse_activity(act)
                act = act.lower()
                self.parameters.append(act)
            m = LTLModel()
            m.parse_from_string(formula)
            m.parameters = self.parameters
        except (TypeError, RuntimeError):
            raise TypeError("Mismatched number of parameters or type")
        return m

