from abc import abstractmethod
import typing
import re
import warnings


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

    # Defining functions
    DECL_ACTIVITY = "activity"
    DECL_BIND = "bind"

    # Defining attributes types
    DECL_INTEGER_BETWEEN = "integer between"
    DECL_FLOAT_BETWEEN = "float between"
    DECL_ENUMERATION = "enumeration"
    DECL_ATTRIBUTE_TYPES = [DECL_INTEGER_BETWEEN, DECL_FLOAT_BETWEEN, DECL_ENUMERATION]

    # Defining constraints functions
    DECL_POSITION = "pos"
    DECL_NEG_POSITION = "!" + DECL_POSITION
    DECL_POSITION_ATTRIBUTES = ["Activity", "Position", "Time"]
    DECL_PAYLOAD = "payload"
    DECL_NEG_PAYLOAD = "!" + DECL_PAYLOAD
    DECL_PAYLOAD_ATTRIBUTES = ["Attribute", "Value", "Position"]
    DECL_CONDITIONAL = "conditional"
    DECL_FUNCTION_PATTERN = r"(!?pos[(][^,]+,\s*(-?\d+|:[^:,]+),\s*(-?\d+|:[^:,]+)[)]|!?payload[(][^,]+,\s*[^,]+,\s*(-?\d+|:[^[,:]+)[)])"

    # Defining conditional constraint values
    DECL_CONDITIONAL_OPERATORS = ["==", "!=", ">=", "<=", ">", "<"]
    DECL_CONDITIONAL_VARIABLE_PATTERN = r"(:?\w+|\d+[.\d+]?)\s*(==|!=|>=|<=|>|<)\s*(:?\w+|\d+[.\d+]?)"

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
    def is_constraint_line(cls, line: str) -> bool:
        """
        Checks if the line is starts with a constraint definition and returns True or False accordingly
        """
        line = line.strip().lower()
        return (re.match(r"^" + cls.DECL_CONDITIONAL_VARIABLE_PATTERN, line, re.IGNORECASE) is not None or
                line.startswith(cls.DECL_POSITION) or
                line.startswith(cls.DECL_NEG_POSITION) or
                line.startswith(cls.DECL_PAYLOAD) or
                line.startswith(cls.DECL_NEG_PAYLOAD))

    @classmethod
    def parse_constraint_line(cls, line: str) -> typing.List[typing.Dict[str, any]]:
        """
        Parses the constraint line and returns a list of constraints
        """

        # removes spaces and double negations from the string and joins the string into one without spaces
        # unparsed_constraints = line = "".join(line.replace("!!", "").split())
        line = line.replace("!!", "")
        unparsed_constraints = "".join(line.split())

        # Initializes the list
        constraints_data: typing.List[typing.Dict[str, str]] = []

        # For every declare function found defined in the constraint
        # Use the regex that recognizes the function and extract the information
        for declare_constraint in re.findall(cls.DECL_FUNCTION_PATTERN, line, re.IGNORECASE):
            # Remove the constraint from the unparsed constraint String
            unparsed_constraints = unparsed_constraints.replace("".join(declare_constraint[0].split()), "")
            # Detect the type
            constraint_type, negated = cls.__find_constraint_type(declare_constraint[0])
            # Extract the values of the constraint and filter them
            values = cls.__filter_elements(declare_constraint[0].split("(")[1].replace(")", "").split(","))
            # Append the data found
            constraints_data.append({"Type": constraint_type, "Negated": negated, "Values": values})

        # For every conditional constraint found
        # Use the regex that recognizes the conditional constraint and extract the information
        for conditional_constraint in re.findall(cls.DECL_CONDITIONAL_VARIABLE_PATTERN, line, re.IGNORECASE):
            # Filter the values
            values = cls.__filter_elements(conditional_constraint)
            # Remove the constraint from the unparsed constraint String
            unparsed_constraints = unparsed_constraints.replace("".join(values), "")
            # Append the data found
            constraints_data.append({"Type": cls.DECL_CONDITIONAL, "Negated": False, "Values": values})

        # Split and filter the unparsed constraint list in order to check if some constraint where not recognized
        # If some where not recognized launch a warning
        unparsed_constraints = cls.__filter_elements(unparsed_constraints.split(","))
        if len(unparsed_constraints) != 0:
            warnings.warn(f"\nCouldn't parse some constraints: {unparsed_constraints}. make sure they respect the correct declaration")

        # Return the parsed constraints
        return constraints_data

    @classmethod
    def __find_constraint_type(cls, constraint: str) -> (str, bool):
        """
        Finds the constraint type of given constraint.
        """

        constraint = constraint.lower()
        # !payload(x, x, x)
        if constraint.find(cls.DECL_NEG_PAYLOAD) != -1:
            return cls.DECL_PAYLOAD, True
        # !pos(x, x, x)
        elif constraint.find(cls.DECL_NEG_POSITION) != -1:
            return cls.DECL_POSITION, True
        # pos(x, x, x)
        elif constraint.find(cls.DECL_POSITION) != -1:
            return cls.DECL_POSITION, False
        # payload(x, x, x)
        elif constraint.find(cls.DECL_PAYLOAD) != -1:
            return cls.DECL_PAYLOAD, False
        # Else error
        else:
            raise ValueError("Could not find the constraint type")

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
    # print(DeclareFunctions.parse_constraint_line(":V1==:V2, pos(actv, 1, 1), 1<:V2, 1==:V2, !pos(actv, 12, 12), :V1==e, pos(actv, 13, 3), payload(actv, erer, 1), :V1==:V2"))
    # print(DeclareFunctions.parse_constraint_line("pos(ER Registration, 1, 1), payload(org:group, 1, :V1), pos(ER Sepsis Triage, 2, 3), payload(org:group, 2, :V2), :V1 == :V2"))

    pass
