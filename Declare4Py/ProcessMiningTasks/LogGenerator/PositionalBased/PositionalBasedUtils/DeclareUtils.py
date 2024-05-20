from abc import abstractmethod
import typing
import re
import warnings
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.ASPUtils import ASPFunctions


class DeclareEntity:
    """
    An Abstract DeclareEntity that has to define a to_asp method
    """

    @abstractmethod
    def to_declare(self) -> str:
        pass


class DeclareFunctions:
    """
    DeclareFunctions defines functions and constants for DECLARE
    """

    # Defining decl functions
    DECL_ACTIVITY = "activity"
    DECL_BIND = "bind"

    # Defining attributes types
    DECL_INTEGER_BETWEEN = "integer between"
    DECL_FLOAT_BETWEEN = "float between"
    DECL_ENUMERATION = "enumeration"
    DECL_ATTRIBUTE_TYPES = [DECL_INTEGER_BETWEEN, DECL_FLOAT_BETWEEN, DECL_ENUMERATION]

    # Defining constraints functions
    DECL_POSITION = "pos"
    DECL_ABSOLUTE_POSITION = "absolute_pos"
    DECL_PAYLOAD = "payload"
    DECL_ABSOLUTE_PAYLOAD = "absolute_payload"
    DECL_PAYLOAD_RANGE = "payload_range"
    DECL_CONDITIONAL = "conditional"

    # Defining the order of importance for the constraint function search during parsing
    DECL_CONSTRAINT_FUNCTIONS = [
        DECL_ABSOLUTE_POSITION,
        DECL_POSITION,
        DECL_ABSOLUTE_PAYLOAD,
        DECL_PAYLOAD_RANGE,
        DECL_PAYLOAD,
        DECL_CONDITIONAL
    ]

    # Defining Functions arguments types
    DECL_INT_ARG = "int"
    DECL_FLOAT_ARG = "float"
    DECL_INT_OR_FLOAT_ARG = "int or float"
    DECL_ANY_ARG = "any"
    DECL_ENCODE_ARG = "encode"

    # Defining function input arguments types
    DECL_POSITION_ARGS_TYPE = DECL_NEG_POSITION_ARGS_TYPE = [DECL_ENCODE_ARG, DECL_INT_ARG, DECL_INT_ARG]
    DECL_PAYLOAD_ARGS_TYPE = DECL_NEG_PAYLOAD_ARGS_TYPE = [DECL_ENCODE_ARG, DECL_ANY_ARG, DECL_INT_ARG]
    DECL_PAYLOAD_RANGE_ARGS_TYPE = [DECL_ENCODE_ARG, DECL_INT_OR_FLOAT_ARG, DECL_INT_OR_FLOAT_ARG, DECL_INT_ARG]
    DECL_ABSOLUTE_POSITION_ARGS_TYPE = [DECL_ENCODE_ARG, DECL_INT_ARG, DECL_INT_ARG]
    DECL_ABSOLUTE_PAYLOAD_ARGS_TYPE = [DECL_ENCODE_ARG, DECL_ANY_ARG]

    # Defining constraint regex pattern
    DECL_POSITION_PATTERN = r"!?pos[(][^,]+,[^,]+,[^,]+[)]"
    DECL_ABSOLUTE_POSITION_PATTERN = r"absolute_pos[(][^,]+,[^,]+,[^,]+[)]"
    DECL_PAYLOAD_PATTERN = r"!?payload[(][^,]+,[^,]+,[^,]+[)]"
    DECL_PAYLOAD_RANGE_PATTERN = r"payload_range[(][^,]+,[^,]+,[^,]+,[^,]+[)]"
    DECL_ABSOLUTE_PAYLOAD_PATTERN = r"absolute_payload[(][^,]+,[^,]+[)]"
    DECL_CONDITIONAL_VARIABLE_PATTERN = r"(\w[\w.]+|:?\w+)\s*(([+]|-)\s*(\w[\w.]+|:?\w+))?\s*(==|!=|>=|<=|>|<)\s*(\w[\w.]+|:?\w+)\s*(([+]|-)\s*(\w[\w.]+|:?\w+))?"

    # Defining the order of importance for the constraint pattern, Otherwise some pattern might find themselves in other patterns
    DECL_CONSTRAINT_PATTERNS = [
        DECL_ABSOLUTE_POSITION_PATTERN,
        DECL_POSITION_PATTERN,
        DECL_ABSOLUTE_PAYLOAD_PATTERN,
        DECL_PAYLOAD_RANGE_PATTERN,
        DECL_PAYLOAD_PATTERN,
        DECL_CONDITIONAL_VARIABLE_PATTERN
    ]

    DECL_CONSTRAINT_FUNCTIONS_DICT = {
        DECL_POSITION: {
            "Type": DECL_POSITION,
            "Negated": False,
            "ArgsType": DECL_POSITION_ARGS_TYPE.copy(),
            "Pattern": DECL_POSITION_PATTERN,
            "ASPFunction": ASPFunctions.ASP_TIMED_EVENT,
            "ASPFormat": ASPFunctions.ASP_TIME_EVENT_FORMAT,
            "AbsoluteRule": False,
            "ASPRule": None,
            "ASPRuleFormat": None
        },
        DECL_ABSOLUTE_POSITION: {
            "Type": DECL_ABSOLUTE_POSITION,
            "Negated": False,
            "ArgsType": DECL_ABSOLUTE_POSITION_ARGS_TYPE.copy(),
            "Pattern": DECL_ABSOLUTE_POSITION_PATTERN,
            "ASPFunction": ASPFunctions.ASP_TIMED_EVENT,
            "ASPFormat": {"2": ASPFunctions.ASP_TIME_EVENT_FORMAT.format("{}", "{}", "_"), "3": ASPFunctions.ASP_TIME_EVENT_FORMAT},
            "AbsoluteRule": True,
            "ASPRule": {"2": ASPFunctions.ASP_FIXED_EVENT, "3": ASPFunctions.ASP_FIXED_TIME_EVENT},
            "ASPRuleFormat": {"2": ASPFunctions.ASP_FIXED_EVENT_FORMAT, "3": ASPFunctions.ASP_FIXED_TIME_EVENT_FORMAT}
        },
        DECL_PAYLOAD: {
            "Type": DECL_PAYLOAD,
            "Negated": False,
            "ArgsType": DECL_PAYLOAD_ARGS_TYPE.copy(),
            "Pattern": DECL_PAYLOAD_PATTERN,
            "ASPFunction": ASPFunctions.ASP_ASSIGNED_VALUE,
            "ASPFormat": ASPFunctions.ASP_ASSIGNED_VALUE_FORMAT,
            "AbsoluteRule": False,
            "ASPRule": None,
            "ASPRuleFormat": None
        },
        DECL_ABSOLUTE_PAYLOAD: {
            "Type": DECL_ABSOLUTE_PAYLOAD,
            "Negated": False,
            "ArgsType": DECL_ABSOLUTE_PAYLOAD_ARGS_TYPE.copy(),
            "Pattern": DECL_ABSOLUTE_PAYLOAD_PATTERN,
            "ASPFunction": ASPFunctions.ASP_ASSIGNED_VALUE,
            "ASPFormat": ASPFunctions.ASP_ASSIGNED_VALUE_FORMAT.format("{}", "{}", "_"),
            "AbsoluteRule": True,
            "ASPRule": ASPFunctions.ASP_FIXED_PAYLOAD,
            "ASPRuleFormat": ASPFunctions.ASP_FIXED_PAYLOAD_FORMAT
        },
        DECL_PAYLOAD_RANGE: {
            "Type": DECL_PAYLOAD_RANGE,
            "Negated": False,
            "ArgsType": DECL_PAYLOAD_RANGE_ARGS_TYPE.copy(),
            "Pattern": DECL_PAYLOAD_RANGE_PATTERN,
            "ASPFunction": ASPFunctions.ASP_ASSIGNED_VALUE,
            "ASPFormat": ASPFunctions.ASP_ASSIGNED_VALUE_RANGE_FORMAT,
            "AbsoluteRule": False,
            "ASPRule": None,
            "ASPRuleFormat": None
        },
        DECL_CONDITIONAL: {
            "Type": DECL_CONDITIONAL,
            "Negated": False,
            "ArgsType": None,
            "Pattern": DECL_CONDITIONAL_VARIABLE_PATTERN,
            "ASPFunction": None,
            "ASPFormat": None,
            "AbsoluteRule": False,
            "ASPRule": None,
            "ASPRuleFormat": None
        },
    }

    # Defining conditional constraint values
    DECL_CONDITIONAL_OPERATORS = ["==", "!=", ">=", "<=", ">", "<"]

    # Defining file extension
    DECL_FILE_EXTENSION = ".decl"

    @classmethod
    def is_activation_line(cls, line: str) -> bool:
        """
        Checks if the line is an activation line and if it respects the ': ' rule
        """

        # If the line does not start with 'activity' false
        if not line.strip().lower().startswith(cls.DECL_ACTIVITY):
            return False

        # Searches for the separation ': '.
        # Activities cannot contain such sequence of characters
        if line.find(": ") != -1:
            raise ValueError("Activation Line cannot contain the sequence of characters ': ' (colon followed by a space)")

        return True

    @classmethod
    def parse_activation_line(cls, line: str) -> typing.List[str]:
        """
        Parses the activation line and returns a list of activity names
        """

        # Parses te activation line. the word activity is removed together with the separator and then the activities ar split using a comma
        line = re.compile(re.escape(cls.DECL_ACTIVITY), re.IGNORECASE).sub("", line, 1).split(",")
        # Every activity is then mapped, filtered and returned
        return cls.__filter_elements(line)

    @classmethod
    def is_bind_line(cls, line: str) -> bool:
        """
        Checks if the line is a bind line and if it respects the ': ' rule
        """

        # If the line does not start with 'bind' false
        if not line.strip().lower().startswith(cls.DECL_BIND):
            return False

        # Searches for the separation ': '
        if line.find(": ") == -1:
            raise ValueError(f"Could not find the sequence of characters ': ' that divides activities from attributes. EX: act_1, ..., act_n: attr_1, ..., attr_n")

        # Checks if the only one separator exists ': '
        if len(line.split(": ")) > 2:
            raise ValueError(f"The sequence of characters ': ' is present more than 1 time. Cannot distinguish the division of activities and attributes EX: act_1, ..., act_n: attr_1, ..., attr_n")

        return True

    @classmethod
    def parse_bind_line(cls, line: str) -> (typing.List[str], typing.List[str]):
        """
        Parses the bind line and returns a list of activity names and a list of attribute names
        """

        # The bind keyword is removed and the list is split using the separator ': '
        line = re.compile(re.escape(cls.DECL_BIND), re.IGNORECASE).sub("", line, 1).split(": ")

        # The line is split in 2 and each split is then split again using the comma as a separator
        # The first split are activities and the second split are attributes
        activities = line[0].split(",")
        attributes = line[1].split(",")

        # Every activity and attributes is then mapped, filtered and returned
        return cls.__filter_elements(activities), cls.__filter_elements(attributes)

    @classmethod
    def is_attribute_line(cls, line: str) -> bool:
        """
        Checks if the line is an attribute definition line and if it respects the ': ' rule
        """

        # Searches for the separation ': '
        if line.find(": ") == -1:
            return False

        # Checks if the only one separator exists ': '
        if len(line.split(": ")) > 2:
            raise ValueError(f"The sequence of characters ': ' is present more than 1 time. Cannot distinguish the division of attributes and values EX: attr_1, ..., attr_n: val_1, ..., val_n")

        return True

    @classmethod
    def is_declare_attribute_type(cls, attribute_type: str) -> bool:
        """
        Returns true if the attribute type is a defined attribute
        """
        return attribute_type in cls.DECL_ATTRIBUTE_TYPES

    @classmethod
    def parse_attribute_line(cls, line: str) -> (typing.List[str], str, typing.List[str]):
        """
        Parses the attribute line and returns a list of attribute names and values and the type of the attributes
        """

        # Splits the line between the attributes and the values using the separator ': ' as a split
        line = line.split(": ")

        # Splits the Attributes using a comma as a separator
        attributes = line[0].split(",")

        # Strips the values
        values = line[1].strip()

        # If the value starts with integer between it defines a integer range
        if values.startswith(cls.DECL_INTEGER_BETWEEN):
            # Parses the integer range values
            values = values.lower().replace(cls.DECL_INTEGER_BETWEEN, "").split("and")
            # The attribute type becomes integer range
            attribute_type = cls.DECL_INTEGER_BETWEEN

        # If the value starts with float between it defines a float range
        elif values.startswith(cls.DECL_FLOAT_BETWEEN):
            # Parses the float range values
            values = values.lower().replace(cls.DECL_FLOAT_BETWEEN, "").split("and")
            # The attribute type becomes float range
            attribute_type = cls.DECL_FLOAT_BETWEEN

        # Otherwise it is an enumeration
        else:
            # The values are split using a comma as a separator
            values = values.split(",")
            # The attribute type becomes Enumeration
            attribute_type = cls.DECL_ENUMERATION

        # The list of filtered Attributes, the type and the list of filtered values are then returned
        return cls.__filter_elements(attributes), attribute_type, cls.__filter_elements(values)

    @classmethod
    def has_constraints_in_line(cls, line: str) -> bool:
        """
        Checks if the line is starts with a constraint definition and returns True or False accordingly
        """
        for pattern in cls.DECL_CONSTRAINT_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE) is not None:
                return True

        return False

    @classmethod
    def parse_constraint_line(cls, line: str) -> typing.List[typing.Dict[str, any]]:
        """
        Parses the constraint line and returns a list of constraints
        """
        #TODO RICOOMENTARE

        # removes spaces and double negations from the string and joins the string into one without spaces
        # unparsed_constraints = line = "".join(line.replace("!!", "").split())
        line = line.replace("!!", "")
        unparsed_constraints = "".join(line.split())

        # Initializes the list
        constraints_data: typing.List[typing.Dict[str, str]] = []

        for decl_function in cls.DECL_CONSTRAINT_FUNCTIONS:

            if decl_function == cls.DECL_CONDITIONAL:
                continue

            pattern = cls.DECL_CONSTRAINT_FUNCTIONS_DICT[decl_function]["Pattern"]
            # For every declare function found defined in the constraint
            # Use the regex that recognizes the function and extract the information
            for declare_constraint in re.findall(pattern, line, re.IGNORECASE):

                function_dict: typing.Dict[str, any] = dict(cls.DECL_CONSTRAINT_FUNCTIONS_DICT[decl_function])
                function_dict["ArgsType"] = function_dict["ArgsType"].copy()
                function_dict["Negated"] = declare_constraint.startswith("!")

                # Remove the constraint from the unparsed constraint String
                unparsed_constraints = unparsed_constraints.replace("".join(declare_constraint.split()), "", 1)
                # Extract the values of the constraint and filter them
                values = cls.__filter_elements(declare_constraint.split("(")[1].replace(")", "").split(","))

                if function_dict["AbsoluteRule"]:
                    cls.__parse_absolute_rule_dict(function_dict, values)

                function_dict["Values"] = values
                # Append the data found
                constraints_data.append(function_dict)

        # For every conditional constraint found
        # Use the regex that recognizes the conditional constraint and extract the information
        for conditional_constraint in re.findall(cls.DECL_CONDITIONAL_VARIABLE_PATTERN, line, re.IGNORECASE):

            function_dict = dict(cls.DECL_CONSTRAINT_FUNCTIONS_DICT[cls.DECL_CONDITIONAL])

            # Filter the values
            values = cls.__filter_elements(conditional_constraint)
            values = cls.__filter_conditional_constraint_arguments(values)
            # Remove the constraint from the unparsed constraint String
            unparsed_constraints = unparsed_constraints.replace("".join("".join(values).split()), "", 1)

            function_dict["Values"] = values

            # Append the data found
            constraints_data.append(function_dict)

        # Split and filter the unparsed constraint list in order to check if some constraint where not recognized
        # If somewhere not recognized launch a warning
        unparsed_constraints = cls.__filter_elements(unparsed_constraints.split(","))
        if len(unparsed_constraints) != 0:
            warnings.warn(f"\nCouldn't parse some constraints: {unparsed_constraints}. make sure they respect the correct declaration")

        # Return the parsed constraints
        return constraints_data

    @classmethod
    def __parse_absolute_rule_dict(cls,  function_dict: typing.Dict[str, any], values: typing.List[str]):

        if function_dict["Type"] == cls.DECL_ABSOLUTE_POSITION:
            if values[2] == "_":
                values.pop(2)
                function_dict["ArgsType"].pop(2)

            num_args = str(len(values))
            function_dict["ASPFormat"] = function_dict["ASPFormat"][num_args]
            function_dict["ASPRule"] = function_dict["ASPRule"][num_args]
            function_dict["ASPRuleFormat"] = function_dict["ASPRuleFormat"][num_args]


    # TODO Comment Code ? Migliorare? Sistemare?
    @classmethod
    def __filter_conditional_constraint_arguments(cls, elements: typing.List[str]) -> typing.List[str]:

        if len(elements) < 3:
            raise ValueError(f"Conditional Constraint must have at least 3 arguments. Found {elements}")

        if len(elements) == 3:
            return elements

        index_to_remove = []
        for index, el in enumerate(elements):
            if el.startswith("+") and el != "+":
                index_to_remove.append(index)
            if el.startswith("-") and el != "-":
                index_to_remove.append(index)

        index_to_remove.reverse()
        for index in index_to_remove:
            elements.pop(index)

        return elements

    @classmethod
    def is_comment_line(cls, line: str) -> bool:
        """
        Returns True if the line is a comment line or an empty line, False otherwise.
        """
        return line.strip().startswith("#") or len(line) == 0

    @classmethod
    def __filter_elements(cls, elements: typing.List[str]) -> typing.List[str]:
        """
        Method used to filter a list of String elements.
        First it is mapped using the method .strip() on each string
        Them is filtered by removing empty strings
        """
        return list(filter(lambda el: len(el) > 0, map(lambda el: el.strip(), elements)))


if __name__ == "__main__":
    # print(DeclareFunctions.is_activation_line("ACTIvity ER Registration, Er triage, org:group:,,  ,"))
    # print(DeclareFunctions.parse_activation_line("ACTIvity ER Registration, Er activity triage, org:group:,,  ,"))
    # print(DeclareFunctions.has_constraints_in_line("pos(1,2,3), payload(1,2,3)"))
    import pprint as p
    p.pprint(DeclareFunctions.parse_constraint_line("absolute_pos(Er Triage, 2, _), absolute_payload(org:group, 1), !payload(org:group, 1, :V1), pos(ER Sepsis Triage, 2, _), :V2 + 1< :V2, 1==:V2 + 10, :V1 + 10 == 30 + :V2, 1-:V1 ==:V2"))
    # print(DeclareFunctions.parse_constraint_line("pos(ER Registration, 1, 1), payload(org:group, 1, :V1), pos(ER Sepsis Triage, 2, 3), payload(org:group, 2, :V2), :V1 == :V2"))

    pass
