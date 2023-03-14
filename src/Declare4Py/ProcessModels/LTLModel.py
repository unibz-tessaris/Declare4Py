from abc import ABC

from src.Declare4Py.ProcessModels.AbstractModel import ProcessModel

from pylogics.parsers import parse_ltl


# Basic LTL formulae for user
def eventually_activity_A(activity: str):
    formula_str = "F(" + activity + ")"
    return formula_str


def eventually_A_then_B(activity1: str, activity2: str):
    formula_str = "F(" + activity1 + " -> F(" + activity2 + "))"
    return formula_str


def eventually_A_or_B(activity1: str, activity2: str):
    formula_str = "F(" + activity1 + ") || F(" + activity2 + ")"
    return formula_str


def eventually_A_next_B(activity1: str, activity2: str):
    formula_str = "F(" + activity1 + " -> X(" + activity2 + "))"
    return formula_str


def eventually_A_then_B_then_C(activity1: str, activity2: str, activity3: str):
    formula_str = "F(" + activity1 + " -> F(" + activity2 + " -> F(" + activity3 + ")))"
    return formula_str


def eventually_A_next_B_next_C(activity1: str, activity2: str, activity3: str):
    formula_str = "F(" + activity1 + " -> X(" + activity2 + " -> X(" + activity3 + ")))"
    return formula_str


def next_A(act: str):
    formula_str = "X(" + act + ")"
    return formula_str


class LTLModelTemplate:
    """
    Class that allows the user to create a template. User can choose between various standard formulae.
    Makes use of the class LTLModel
    """
    templates = {'eventually_activity_A': eventually_activity_A, 'eventually_A_then_B': eventually_A_then_B,
                 'eventually_A_or_B': eventually_A_or_B, 'eventually_A_next_B': eventually_A_next_B,
                 'eventually_A_then_B_then_C': eventually_A_then_B_then_C,
                 'eventually_A_next_B_next_C': eventually_A_next_B_next_C, 'next_A': next_A}
    templ_str: str = None

    def __init__(self, templ_str: str):
        if templ_str in self.templates:
            self.templ_str = templ_str
        else:
            raise RuntimeError("Inserted parameter is not of type string or is not a template")

    def get_templ_model(self, *activities):
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
            m = LTLModel()
            m.parse_from_string(formula)
        except (TypeError, RuntimeError):
            raise TypeError("Mismatched number of parameters")
        return m


class LTLModel(ProcessModel, ABC):

    def __init__(self):
        super().__init__()
        self.formula: str = ""
        self.parsed_formula = None

    def parse_from_string(self, content: str, new_line_ctrl: str = "\n"):
        """
        This function expects an LTL formula as a string.
        The pylogics library is used, reference to it in case of doubt.
        Refer to https://marcofavorito.me/tl-grammars/v/7d9a17267fbf525d9a6a1beb92a46f05cf652db6/ LTL symbols that are allowed.
        We allow unary operators only if followed by parenthesis, e.g.: G(a), X(a), etc..


        Args:
            content: string containing the LTL formula to be passed
            new_line_ctrl:

        Returns:
            The parsed LTL formula

        """
        parsed = None
        if type(content) is not str:
            raise RuntimeError("You must specify a string as input formula.")

        int_char_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h', 8: 'i', 9: 'l'}

        unary_operators = {"g(": "G(", "x(": "X(", "f(": "F(", "x[!](": "X[!]("}

        binary_operators = {" u ": " U ", "u(": "U(", " r ": " R ", "r(": "R(", " w ": " W ",
                            "w(": "W(", " m ": " M ", "m(": "M(", " v ": " V ", "v(": "V("}

        for int_key in int_char_map.keys():
            content = content.replace(str(int_key), int_char_map[int_key])

        content = content.lower()

        for key, value in unary_operators.items():
            content = content.replace(key, value)

        for key, value in binary_operators.items():
            content = content.replace(key, value)

        try:
            parsed = parse_ltl(content)
        except RuntimeError:
            raise RuntimeError(f"The inserted string: \"{content}\" is not a valid LTL formula")

        self.formula = content
        self.parsed_formula = parsed
