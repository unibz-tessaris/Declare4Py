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

    # Defining the attribute type characteristics
    class DeclAttributeType:
        """
        Class that defines an attributes arguments characteristics for DECLARE functions
        """

        # Constructor
        def __init__(self, name: str, decl_type: str, can_be_var: bool = True, can_have_op: bool = True, can_be_empty: bool = True):
            """
            Parameters
                name: Name of the attribute
                decl_type: Type of the attribute
                can_be_var: Whether the attribute can be a variable or constant
                can_have_op: Whether the attribute can have conditional operators
                can_be_empty: Whether the attribute can be empty
            """
            # Decides which type of operator are allowed based on the type
            if decl_type == "encode" and can_have_op:
                op_allowed = ["!="]
            elif decl_type == "encode" or not can_have_op:
                op_allowed = []
            else:
                op_allowed = ["==", "!=", ">=", "<=", ">", "<"]

            # Initializing information
            self.name = name
            self.decl_type = decl_type
            self.can_be_var = can_be_var
            self.op_allowed = op_allowed
            self.can_have_op = can_have_op
            self.can_be_empty = can_be_empty

        def to_dict(self):
            """
            Returns the Attribute type dict information
            """
            return {"name": self.name, "decl_type": self.decl_type, "can_be_var": self.can_be_var, "op_allowed": self.op_allowed, "can_have_op": self.can_have_op, "can_be_empty": self.can_be_empty}

    # Defining conditional constraint values
    DECL_CONDITIONAL_OPERATORS = ["==", "!=", ">=", "<=", ">", "<"]

    # Defining Functions arguments types
    DECL_INT_ARG = "int"
    DECL_FLOAT_ARG = "float"
    DECL_INT_OR_FLOAT_ARG = "int or float"
    DECL_ANY_ARG = "any"
    DECL_ENCODE_ARG = "encode"

    # The following declaration initializes each argument type of each function argument
    # function = [arg_1, ..., arg_n]

    # Function pos; Arguments type information:
    DECL_POSITION_ARGS_TYPE = [
        DeclAttributeType("Activity", DECL_ENCODE_ARG, can_be_empty=False),
        DeclAttributeType("Position", DECL_INT_ARG),
        DeclAttributeType("Time", DECL_INT_ARG)
    ]
    # Function payload; Arguments type information:
    DECL_PAYLOAD_ARGS_TYPE = [
        DeclAttributeType("Attribute", DECL_ENCODE_ARG, can_be_empty=False),
        DeclAttributeType("Value", DECL_ANY_ARG, can_be_empty=False),
        DeclAttributeType("Position", DECL_INT_ARG)
    ]
    # Function payload_range; Arguments type information:
    DECL_PAYLOAD_RANGE_ARGS_TYPE = [
        DeclAttributeType("Attribute", DECL_ENCODE_ARG, can_have_op=False, can_be_empty=False),
        DeclAttributeType("Min_value", DECL_INT_OR_FLOAT_ARG, can_be_var=False, can_have_op=False),
        DeclAttributeType("Max_value", DECL_INT_OR_FLOAT_ARG, can_be_var=False, can_have_op=False),
        DeclAttributeType("Position", DECL_INT_ARG)
    ]
    # Function absolute_position; Arguments type information:
    DECL_ABSOLUTE_POSITION_ARGS_TYPE = [
        DeclAttributeType("Activity", DECL_ENCODE_ARG, can_have_op=False, can_be_empty=False),
        DeclAttributeType("Position", DECL_INT_ARG, can_have_op=False, can_be_empty=False),
        DeclAttributeType("Time", DECL_INT_ARG, can_have_op=False)
    ]
    # Function absolute_payload; Arguments type information:
    DECL_ABSOLUTE_PAYLOAD_ARGS_TYPE = [
        DeclAttributeType("Attribute", DECL_ENCODE_ARG, can_have_op=False, can_be_empty=False),
        DeclAttributeType("Value", DECL_ANY_ARG, can_have_op=False, can_be_empty=False)
    ]

    # Defining constraint regex pattern
    DECL_POSITION_PATTERN = r"!?pos[(][^,]+,[^,]+,[^,]+[)]"
    DECL_ABSOLUTE_POSITION_PATTERN = r"absolute_pos[(][^,]+,[^,]+,[^,]+[)]"
    DECL_PAYLOAD_PATTERN = r"!?payload[(][^,]+,[^,]+,[^,]+[)]"
    DECL_PAYLOAD_RANGE_PATTERN = r"payload_range[(][^,]+,[^,]+,[^,]+,[^,]+[)]"
    DECL_ABSOLUTE_PAYLOAD_PATTERN = r"absolute_payload[(][^,]+,[^,]+[)]"
    DECL_CONDITIONAL_VARIABLE_PATTERN = r"(\w[\w.]+|:?\w+)\s*(([+]|-)\s*(\w[\w.]+|:?\w+))?\s*(==|!=|>=|<=|>|<)\s*(\w[\w.]+|:?\w+)\s*(([+]|-)\s*(\w[\w.]+|:?\w+))?"
    DECL_INTEGER_OR_FLOAT_PATTERN = r"\d+(.\d+)?"

    # Defining the order of importance for the constraint pattern, Otherwise some pattern might find themselves in other patterns
    DECL_CONSTRAINT_PATTERNS = [
        DECL_ABSOLUTE_POSITION_PATTERN,
        DECL_POSITION_PATTERN,
        DECL_ABSOLUTE_PAYLOAD_PATTERN,
        DECL_PAYLOAD_RANGE_PATTERN,
        DECL_PAYLOAD_PATTERN,
        DECL_CONDITIONAL_VARIABLE_PATTERN
    ]
    """
    The following declarations initializes for each function the dict information
    
    function dict = {
        The name of the function : {
            "Type": The name of the function: pos, payload, payload_range, absolute_pos, absolute_payload
            "Negated": Whether the function is negated
            "ArgsType": The arguments type information
            "Pattern": The pattern that recognizes the function
            "ASPFunction": The corresponding ASP function name
            "ASPFormat": The corresponding ASP function format in which the future information will be inserted
            "AbsoluteRule": Whether the function has some absolute rule to define or not
            "ASPRule": The corresponding ASP rule name
            "ASPRuleFormat": The corresponding ASP rule format in which the future information will be inserted
        },
        etc ... 
    }
    
    When the function has a dict in ASPFormat, ASPRule, ASPRuleFormat there is an occurrence of function overload
    Meaning that during the parsing the correct rule and formats must be selected
    """

    DECL_CONSTRAINT_FUNCTIONS_DICT = {
        # Function pos
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
        # Function absolute_pos
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
        # Function payload
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
        # Function absolute_payload
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
        # Function payload_range
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
        # constraint conditional
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
    def parse_constraint_line(cls, line: str, model_attributes: typing.Union[None, typing.Dict[str, any]] = None) -> typing.List[typing.Dict[str, any]]:
        """
        Parses the constraint line and returns a list of constraints
        """

        # removes spaces and double negations from the string and joins the string into one without spaces
        # unparsed_constraints = line = "".join(line.replace("!!", "").split())
        line = line.replace("!!", "")
        unparsed_constraints = "".join(line.split())

        # Initializes the constraints_data list
        constraints_data: typing.List[typing.Dict[str, str]] = []

        # For every function in the list of functions
        for decl_function in cls.DECL_CONSTRAINT_FUNCTIONS:

            # If the function is a conditional constraint skip
            if decl_function == cls.DECL_CONDITIONAL:
                continue

            # Otherwise extract the regex pattern
            pattern = cls.DECL_CONSTRAINT_FUNCTIONS_DICT[decl_function]["Pattern"]

            # For every declare function found defined in the constraint
            # Use the regex that recognizes the function and extract the information
            for declare_constraint in re.findall(pattern, line, re.IGNORECASE):

                # Collect a copy of the function information
                function_dict: typing.Dict[str, any] = dict(cls.DECL_CONSTRAINT_FUNCTIONS_DICT[decl_function])
                # Remove the pattern (useless information)
                function_dict.pop("Pattern")
                # Copy the list of Arguments
                function_dict["ArgsType"] = function_dict["ArgsType"].copy()
                # Check if the function is negated
                function_dict["Negated"] = declare_constraint.startswith("!")

                # Remove the constraint from the unparsed constraint String
                unparsed_constraints = unparsed_constraints.replace("".join(declare_constraint.split()), "", 1)

                # Extract the values of the constraint and filter them
                values = cls.__filter_elements(declare_constraint.split("(")[1].replace(")", "").split(","))

                # For each value extracted check if each value matches the requirements: can_be_var, can_have_op, can_be_empty
                try:
                    cls.__check_values_requirements(function_dict["ArgsType"], values)
                except ValueError as ve:
                    raise ValueError(f"Error during the Parse of the constraint {declare_constraint}: {ve}")

                # Parse additional special condition based on the type of declare function
                cls.__parse_additional_conditions(function_dict, values, model_attributes)

                # Store the values
                function_dict["Values"] = values
                # Append the data found
                constraints_data.append(function_dict)

        # For every conditional constraint found
        # Use the regex that recognizes the conditional constraint and extract the information
        for conditional_constraint in re.findall(cls.DECL_CONDITIONAL_VARIABLE_PATTERN, line, re.IGNORECASE):

            # Filter the values
            values = cls.__filter_conditional_constraint_arguments(cls.__filter_elements(conditional_constraint))
            # Remove the constraint from the unparsed constraint String
            unparsed_constraints = unparsed_constraints.replace("".join("".join(values).split()), "", 1)

            # Append the data found
            constraints_data.append({"Type": cls.DECL_CONDITIONAL, "Values": values})

        # Split and filter the unparsed constraint list in order to check if some constraint where not recognized
        # If somewhere not recognized launch a warning
        unparsed_constraints = cls.__filter_elements(unparsed_constraints.split(","))
        if len(unparsed_constraints) != 0:
            warnings.warn(f"\nCouldn't parse some constraints: {unparsed_constraints}. make sure they respect the correct declaration")

        # Return the parsed constraints
        return constraints_data

    @classmethod
    def __check_values_requirements(cls, args_type: typing.List[DeclAttributeType], args: typing.List[str]):
        """
        For each value and corresponding DeclAttributeType searches if the value respects the defined DeclAttributeType rules / constraints
        If some rules are not respected an error will be raised
        """

        # For each arg and argtyp
        for arg, argtype in zip(args, args_type):

            # Check if the arg cannot be a variable and if it is indeed a variable.
            # If both are true an error will be raised
            if not argtype.can_be_var and arg.startswith(":"):
                raise ValueError(f"'Argument {argtype.name} has value {arg} and cannot be variable")

            # Check if the arg cannot be empty and if it is indeed empty.
            # If both are true an error will be raised
            if not argtype.can_be_empty and arg == "_":
                raise ValueError(f"Argument {argtype.name} has value {arg} and cannot be empty")

            # Check if the arg cannot have conditional operators.
            # If the value cannot then the loop searches for conditional operators, and if found will raise an error
            if not argtype.can_have_op:
                for op in cls.DECL_CONDITIONAL_OPERATORS:
                    if arg.startswith(op) or arg.endswith(op):
                        raise ValueError(f"Argument {argtype.name} has value {arg} and cannot have the operator {op} in front or at the end")

            # Check if the arg is of encode type and can have op
            # If the value can then the only op allowed is "!=".
            # If some other are found an error will be raised
            elif argtype.decl_type == cls.DECL_ENCODE_ARG and argtype.can_have_op:
                for op in cls.DECL_CONDITIONAL_OPERATORS:
                    if arg.startswith(op) or arg.endswith(op) and op not in argtype.op_allowed:
                        raise ValueError(f"Argument {argtype.name} has value {arg} and cannot have the operator {op} in front or at the end")

    @classmethod
    def __parse_additional_conditions(cls, function_dict: typing.Dict[str, any], values: typing.List[str], model_attributes: typing.Union[None, typing.Dict[str, any]] = None):
        """
        Parses additional conditional declarations for specific functions
        """

        # Selection of the overloaded ASP rule for the absolute_pos function
        if function_dict["Type"] == cls.DECL_ABSOLUTE_POSITION:

            # If the last value is empty then select the function with 2 arguments
            # Otherwise the function with 3 arguments will be selected
            if values[2] == "_":
                # Remove last value and argtype
                values.pop(2)
                function_dict["ArgsType"].pop(2)

            # number of arguments
            num_args = str(len(values))

            # Storing the correct values
            function_dict["ASPFormat"] = function_dict["ASPFormat"][num_args]
            function_dict["ASPRule"] = function_dict["ASPRule"][num_args]
            function_dict["ASPRuleFormat"] = function_dict["ASPRuleFormat"][num_args]

        # If the function is of type payload range some checks need to be done on the arguments
        elif function_dict["Type"] == cls.DECL_PAYLOAD_RANGE:
            # saves correctly the values in order to recognize them
            attribute_name_arg = values[0]
            min_val_arg = values[1]
            max_val_arg = values[2]

            # If the value is a variable (:VAR) and min or max are empty raise an error
            # This cannot be possible
            if attribute_name_arg.startswith(":") and (min_val_arg == "_" or max_val_arg == "_"):
                raise ValueError("When using a variable in the payload range function, both min and max value must be defined and cannot be _")

            # If the value is a variable check if min or max match the Integer/float regex
            elif attribute_name_arg.startswith(":"):
                # If min or max are not Integers or floats raise an error
                if re.search(cls.DECL_INTEGER_OR_FLOAT_PATTERN, min_val_arg, re.IGNORECASE) is None:
                    raise ValueError(f"When using a variable in the payload range function, min must be a float or integer, found: {min_val_arg}")
                if re.search(cls.DECL_INTEGER_OR_FLOAT_PATTERN, max_val_arg, re.IGNORECASE) is None:
                    raise ValueError(f"When using a variable in the payload range function, max must be a float or integer, found: {max_val_arg}")

            # If the attributes list of the model are not None
            elif model_attributes is not None:

                # Search if the attribute is defined otherwise launch an error
                if attribute_name_arg not in model_attributes.keys():
                    raise ValueError(f"Attribute '{attribute_name_arg}' is not defined")

                # Fetch the attribute and check if the type is enumeration. If it is launch and error: Enumeration cannot have ranges
                attribute = model_attributes[attribute_name_arg]
                if attribute.get_type() == "enumeration":
                    raise ValueError("Invalid attribute tipe for the payload range function. Attribute is of type enumeration")
                # Otherwise only integer or floats ranges are left
                else:
                    # Recover minimal and maximal values
                    min_val, max_val = attribute.get_values()

                    # Try to remove the precision from the min_val_arg or max_val_arg
                    # If the value is integer nothing will happen
                    # If the value is a float the correct precision will be removed and the value returned is the parsed integer
                    # If an error occurs during the parsing then the min_val_arg becomes the min_val or then max_val_arg becomes the max_val
                    try:
                        min_val_arg = attribute.remove_precision(min_val_arg)
                    except ValueError:
                        min_val_arg = min_val
                    try:
                        max_val_arg = attribute.remove_precision(max_val_arg)
                    except ValueError:
                        max_val_arg = max_val

                    # Checks if the values need to be inverted
                    if min_val_arg > max_val_arg:
                        max_val_arg, min_val_arg = min_val_arg, max_val_arg

                    # Checks if the min_val_arg is lower than the minimal value, in case the min_val_arg becomes the min_val
                    if min_val_arg < min_val:
                        min_val_arg = min_val

                    # Checks if the max_val_arg is bigger than the maximal value, in case the max_val_arg becomes the max_val
                    if max_val_arg > max_val:
                        max_val_arg = max_val

                    # Saves the correctly parsed min_val_arg and max_val_arg in the values list
                    values[1] = str(min_val_arg)
                    values[2] = str(max_val_arg)
            else:
                warnings.warn(f"Could not check the consistency of the function payload range with values {values} because the list of attributes of the model was None")

    @classmethod
    def __filter_conditional_constraint_arguments(cls, elements: typing.List[str]) -> typing.List[str]:
        """
        Filters conditional constraint arguments from the elements parsed from the regex groups found in the patterns
        """

        # Conditional constraints have form of:
        # var1 conditional_op var2
        # var1 +- var2 conditional_op var3
        # var1 conditional_op var2 +- var3
        # var1 +- var2 conditional_op var3 +- var4
        # Hence it can have 3, 5 or 7 arguments

        # If the value are lower than 3 raise an error
        if len(elements) < 3:
            raise ValueError(f"Conditional Constraint must have at least 3 arguments. Found {elements}")

        # If 3 then return the elements
        if len(elements) == 3:
            return elements

        # Otherwise remove the non-necessary groups parsed by the regex pattern
        # Save each index
        index_to_remove = []
        for index, el in enumerate(elements):
            if el.startswith("+") and el != "+":
                index_to_remove.append(index)
            if el.startswith("-") and el != "-":
                index_to_remove.append(index)

        # Reverse order of index in order to remove the correct items
        index_to_remove.reverse()
        # Remove the items
        for index in index_to_remove:
            elements.pop(index)

        # return the filtered elements
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


"""
if __name__ == "__main__":
    # print(DeclareFunctions.is_activation_line("activity ER Registration, Er triage, org:group:,,  ,"))
    # print(DeclareFunctions.parse_activation_line("activity ER Registration, Er activity triage, org:group:,,  ,"))
    # print(DeclareFunctions.has_constraints_in_line("pos(1,2,3), payload(1,2,3)"))
    # import pprint as p

    # p.pprint(DeclareFunctions.parse_constraint_line("absolute_pos(Er Triage, 2, _), absolute_payload(org:group, 1), !payload(org:group, 1, :V1), pos(ER Sepsis Triage, 2, _), :V2 + 1< :V2, 1==:V2 + 10, :V1 + 10 == 30 + :V2, 1-:V1 ==:V2"))
    # print(DeclareFunctions.parse_constraint_line("pos(ER Registration, 1, 1), payload(org:group, 1, :V1), pos(ER Sepsis Triage, 2, 3), payload(org:group, 2, :V2), :V1 == :V2"))

    pass
"""