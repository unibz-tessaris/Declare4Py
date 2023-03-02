from abc import ABC

from src.Declare4Py.ProcessModels.AbstractModel import ProcessModel
from pylogics.parsers import parse_ltl


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
        #Usare regex o altro metodo per identificare gli operatori?

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
            print(f"The inserted string: \"{content}\" is not a valid LTL formula")

        self.formula = content
        self.parsed_formula = parsed
