import typing
import warnings

import typing_extensions
import logging
import random
from collections import Counter

from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.ASPUtils import ASPFunctions, ASPEntity
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.DeclareUtils import DeclareFunctions, DeclareEntity
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.PBEncoder import Encoder


class Attribute(ASPEntity, DeclareEntity):
    """
    Represents the Entity Attribute. This Entity is created based on a DECLARE MODEL ATTRIBUTE. It can be converted in ASP.
    """

    # Defines attributes types
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    # Constructor
    def __init__(self, name):
        self.__name: str = name
        self.__type: typing.Union[str, None] = None
        self.__values: typing.List = []
        self.__precision: int = 0

    def parse_values(self, attribute_type: str, attribute_values: typing.List[str]):

        """
        Parses the attribute values to the correct attribute type

        Parameters
            attribute_type: str
                Type of the attribute
            attribute_values: typing.List[str]
                List of all the attributes
        """

        # raises an error if the attribute_type is not a valid declare type
        if not DeclareFunctions.is_declare_attribute_type(attribute_type):
            raise ValueError(f"Attribute is not a declare attribute. The attribute {attribute_type} is not in the list {DeclareFunctions.DECL_ATTRIBUTE_TYPES}")

        # Resets the values list and precision
        self.__values = []
        self.__precision = 0

        # If the value is a float range
        if attribute_type == DeclareFunctions.DECL_FLOAT_BETWEEN:

            # Checks if it has more o less than 2 attributes
            if len(attribute_values) != 2:
                raise ValueError(f"The definition of a {DeclareFunctions.DECL_FLOAT_BETWEEN} requires exactly 2 floats values: min and max. Obtained attribute values: {attribute_values}")

            # Sets the type
            self.__type = Attribute.FLOAT_RANGE

            # Parses the values to floats in order to check also if these 2 values are indeed floats
            # Otherwise it will raise an error
            min_float = float(attribute_values[0])
            max_float = float(attribute_values[1])

            # Checks if the values are inverted
            if min_float > max_float:
                min_float, max_float = max_float, min_float

            # Calculates the precision of min and max a selects biggest precision
            # Ex range 2.0 to 50.00 selects 2 as precision
            precision_min = precision_max = 0
            if attribute_values[0].find(".") != -1:
                precision_min = len(attribute_values[0].split(".")[1])
            if attribute_values[1].find(".") != -1:
                precision_max = len(attribute_values[1].split(".")[1])

            # Sets the precision and calculates the correct corresponding integer values
            self.__precision = precision_max if precision_max > precision_min else precision_min
            self.__values.append(int(min_float * 10 ** self.__precision))
            self.__values.append(int(max_float * 10 ** self.__precision))

            # If the precision is still zero at this point in time then it means that 2 integer values where given
            # Hence the type is changed to integer range
            if self.__precision == 0:
                self.__type = Attribute.INTEGER_RANGE

        elif attribute_type == DeclareFunctions.DECL_INTEGER_BETWEEN:

            # Checks if it has more o less than 2 attributes
            if len(attribute_values) != 2:
                raise ValueError(f"The definition of a {DeclareFunctions.DECL_INTEGER_BETWEEN} requires exactly 2 ints values: min and max. Obtained attribute values: {attribute_values}")

            # Sets the type
            self.__type = Attribute.INTEGER_RANGE

            # Parses the values to floats in order to check also if these 2 values are indeed integers
            # Otherwise it will raise an error
            min_int = int(attribute_values[0])
            max_int = int(attribute_values[1])

            # Checks if the values are inverted
            if min_int > max_int:
                min_int, max_int = max_int, min_int

            # Parses the values to ints in order to check also if these 2 values are indeed ints
            # Otherwise it will raise an error
            self.__values.append(min_int)
            self.__values.append(max_int)

        else:
            # Otherwise the Attribute is an Enumeration and the values are directly stored
            self.__type = Attribute.ENUMERATION
            self.__values = attribute_values
            Encoder().create_and_encode_values(self.__values)

        Encoder().create_and_encode_value(self.__name)

    def get_name(self) -> str:
        """
        Returns the name of the attribute
        """
        return self.__name

    def get_encoded_name(self) -> str:
        """
        Returns the Encoded name of the attribute
        """
        return Encoder.encode_value(self.__name)

    def get_type(self) -> typing.Union[str, None]:
        """
        Returns the type of the attribute
        """
        return self.__type

    def get_values(self) -> typing.Union[typing.List[int], typing.List[str]]:
        """
        Returns the values of the attribute
        """
        return self.__values

    def get_encoded_values(self) -> typing.Union[typing.List[int], typing.List[str]]:
        """
        Returns the encoded values of the attribute
        """
        if self.get_type() == Attribute.ENUMERATION:
            return [Encoder.encode_value(val) for val in self.__values]
        return self.get_values()

    def get_precision(self) -> int:
        """
        Returns the precision of the attribute
        """
        return self.__precision

    def apply_precision(self, value: typing.Union[int, str]) -> float:
        """
        Given an integer value returns the corresponding value float with the applied precision
        """
        return int(value) / 10 ** self.__precision

    def remove_precision(self, value: typing.Union[float, str]) -> int:
        """
        Given a float value returns the corresponding value integer with the removed precision
        """
        return int(float(value) * 10 ** self.__precision)

    def to_asp(self, encoded: bool = False) -> str:
        """
        Converts the attribute to an ASP string and returns the string
        """

        asp = ""

        # Decides based on encoded if the string ASP string must be encoded or not
        # Fetches the corrected data
        if encoded:
            name = self.get_encoded_name()
            values = self.get_encoded_values()
        else:
            name = self.get_name()
            values = self.get_values()

        # If the Attribute is an Enumeration then:
        # Shuffle the items since some times clingo likes to take the last attribute inserted this should give some kind of randomization
        # Append to the current ASP String the values of the attribute
        if self.__type == Attribute.ENUMERATION:
            random.shuffle(values)
            for value in values:
                asp += ASPFunctions.ASP_ATTRIBUTE_VALUE_FORMAT.format(name, value) + ".\n"

        # Otherwise if the Attribute is a range append the range only
        else:
            asp = ASPFunctions.ASP_ATTRIBUTE_RANGE_FORMAT.format(name, self.__values[0], self.__values[1]) + ".\n"

        # Return the ASP string
        return asp

    def to_declare(self) -> str:
        """
        Converts the attribute to a DECLARE string and returns the string
        """

        # Starts by defining the name of the attribute
        decl = self.__name + ": "

        # Appends to the string the attribute range or the sequence of values
        if self.__type == Attribute.INTEGER_RANGE:
            decl += DeclareFunctions.DECL_INTEGER_BETWEEN + " " + str(self.__values[0]) + " and " + str(self.__values[1])
        elif self.__type == Attribute.FLOAT_RANGE:
            decl += DeclareFunctions.DECL_FLOAT_BETWEEN + " " + str(self.__values[0] / 10 ** self.__precision) + " and " + str(self.__values[1] / 10 ** self.__precision)
        else:
            decl += ", ".join(self.__values)

        # Returns the DECLARE string
        return decl

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        """
        Returns the attribute as a dictionary
        """

        # Creates the dictionary
        attr_dict = {
            "name": self.get_name(),
            "type": self.get_type(),
            "values": self.get_values()
        }

        # Creates the keyword precision if the Attribute is a float
        if self.get_type() == Attribute.FLOAT_RANGE:
            attr_dict["precision"] = self.get_precision()

        # Returns the dictionary
        return attr_dict


class Activity(ASPEntity, DeclareEntity):
    """
    Represents the Entity ACTIVITY. This Entity is created based on a DECLARE MODEL ACTIVITY. It can be converted in ASP.
    """

    # Constructor
    def __init__(self, name: str):
        self.__name = name
        self.__attributes: typing.Dict[str, Attribute] = {}
        Encoder().create_and_encode_value(self.__name)

    def get_name(self) -> str:
        """
        Returns the name of the attribute
        """
        return self.__name

    def get_encoded_name(self) -> str:
        """
        Returns the encoded name of the attribute
        """
        return Encoder().encode_value(self.__name)

    def get_attributes(self) -> typing.Dict[str, Attribute]:
        """
        Returns the list of the attributes connected to the activity
        """
        return self.__attributes

    def get_encoded_attributes(self) -> typing.List[str]:
        """
        Returns the list of the encoded attributes connected to the activity
        """
        return Encoder().create_and_encode_values(list(self.__attributes.keys()))

    def set_attribute(self, attribute: typing.Union[str, Attribute]):
        """
        Adds to the list of attributes the new attribute
        """
        if isinstance(attribute, str):
            self.__attributes[attribute] = Attribute(attribute)
        elif isinstance(attribute, Attribute):
            self.__attributes[attribute.get_name()] = attribute
        else:
            raise ValueError(f"Attribute {attribute} is not of type str or Attribute but {type(attribute)}")

    def to_asp(self, encoded: bool = False) -> str:
        """
        Converts the activity to an ASP string and returns the string
        """

        # Decides based on encoded if the string ASP string must be encoded or not
        # Fetches the corrected data
        if encoded:
            name = self.get_encoded_name()
            attributes = self.get_encoded_attributes()
        else:
            name = self.get_name()
            attributes = self.get_attributes().keys()

        # Creates the entry for the ASP activity and appends to the string the connected attributes formatted with the correct ASP function
        asp: str = ASPFunctions.ASP_ACTIVITY_FORMAT.format(name) + ".\n"
        for attribute_name in attributes:
            asp += ASPFunctions.ASP_HAS_ATTRIBUTE_FORMAT.format(name, attribute_name) + ".\n"

        # Returns the ASP String
        return asp

    def to_declare(self) -> str:
        """
        Converts the activity to a DECLARE string and returns the string
        """
        # Parses the name using the DECLARE Activity function
        decl = DeclareFunctions.DECL_ACTIVITY + " " + self.__name + "\n"
        # Parses the attributes using the DECLARE Bind function
        decl += DeclareFunctions.DECL_BIND + " " + self.__name + ": " + ", ".join(self.__attributes.keys())

        # Returns the DECLARE String
        return decl

    def to_dict(self, return_attributes_dict: bool = True) -> typing.Dict[str, typing.Any]:
        """
        Returns the activity as a dictionary
        """

        # If true returns the dictionary of the attributes with the object reference
        if return_attributes_dict:
            attributes = [attr.to_dict() for attr in self.get_attributes().values()]
        # Else returns just the list of the attributes names
        else:
            attributes = list(self.__attributes.keys())

        return {
            "name": self.__name,
            "attributes": attributes
        }


class PBConstraint(ASPEntity, DeclareEntity):
    """
    Represents the Entity CONSTRAINT. This Entity is created based on a DECLARE MODEL CONSTRAINT. It can be converted in ASP.
    """

    # Constructor
    def __init__(self, name: str, model_attributes: typing.Dict[str, Attribute], constraint: str):
        self.__name = f"C{name}"

        # Saves the model Attributes for later usage:
        self.__model_attributes: typing.Dict[str, Attribute] = model_attributes

        # Saves the Declare Constraint
        self.__DECL_constraint: str = constraint

        # Initializes the ASP Absolute Rules
        self.__absolute_rules: typing.List[str] = []
        self.__encoded_absolute_rules: typing.List[str] = []

        # Initializes the ASP Constraints
        self.__ASP_constraints: typing.List[str] = []
        self.__ASP_encoded_constraints: typing.List[str] = []

        # Initializes the Variable and rules lists
        self.__generated_variable_list: typing.List[str] = []
        self.__user_variable_list: typing.List[str] = []
        self.__generated_rule_list: typing.List[str] = []

        # Parses the Constraint
        self.__parse_constraint(constraint)

    def __parse_constraint(self, constraints: str):
        """
        Parses the constraint string using a DECLARE FUNCTION. The function returns a list of dictionaries.
        Each dictionary contains a constraint with his correlated information.
        Each Constraint is then parsed to the correct encoded and non ASP declaration.
        """

        # For each constraint in the line
        for constraint in DeclareFunctions.parse_constraint_line(constraints, self.__model_attributes):

            # If the constraint is conditional: requires a different parsing function
            if constraint["Type"] == DeclareFunctions.DECL_CONDITIONAL:
                cond_const, encoded_cond_const = self.__parse_conditional_constraint(constraint["Values"])
                self.__ASP_constraints.append(cond_const)
                self.__ASP_encoded_constraints.append(encoded_cond_const)
                continue

            # Otherwise each function is parsed using the same method
            # Initializes the list of constraint and encoded constraint and of arguments and encoded arguments
            constraints_list: typing.List[str] = []
            encoded_constraints_list: typing.List[str] = []
            format_args: typing.List[str] = []
            format_encoded_args: typing.List[str] = []

            # Initializes the negation of the constraint
            neg = "not " if constraint["Negated"] else ""
            # Extract the ASP function of the constraint
            asp_format_function = constraint["ASPFormat"]

            # Extracts the arguments type
            args_type: typing.List[DeclareFunctions.DeclAttributeType] = constraint.pop("ArgsType")
            try:
                # For each value in the constraint together with his type
                for value, decl_attr in zip(constraint["Values"], args_type):
                    # Parse the value and the type
                    value, encoded_value, const, encoded_const = self.__parse_function_value(value, decl_attr)
                    # Store each result in the corresponding list
                    format_args.append(value)
                    format_encoded_args.append(encoded_value)
                    constraints_list.append(const)
                    encoded_constraints_list.append(encoded_const)

                # Add to the constraints the ASP function
                self.__ASP_constraints.append(neg + asp_format_function.format(*format_args))
                self.__ASP_encoded_constraints.append(neg + asp_format_function.format(*format_encoded_args))
                # Add to the constraints the extra constraints
                self.__ASP_constraints += self.__filter_elements(constraints_list)
                self.__ASP_encoded_constraints += self.__filter_elements(encoded_constraints_list)

                # If the constraint has an absolute rule
                if constraint["AbsoluteRule"]:

                    # A new rule name is generated
                    rule = self.__generate_new_rule_name()

                    # The name of the absolute rule is extracted toghether with the asp format of the rule
                    rule_name = constraint["ASPRule"]
                    asp_function = constraint["ASPRuleFormat"]

                    # The absolute rule is formated with the values and becomes unique thanks to the new generated rule name
                    # Then both Encoded and not encoded rules are stored
                    self.__absolute_rules.append(rule + "_" + asp_function.format(*format_args))
                    self.__encoded_absolute_rules.append(rule + "_" + asp_function.format(*format_encoded_args))

                    # Sequentially the constraint of the absolute rule must be added to the constraint list
                    self.__ASP_constraints.append("not " + rule + "_" + rule_name)
                    self.__ASP_encoded_constraints.append("not " + rule + "_" + rule_name)

                # Catch any errors and raise them above with extra message
            except (ValueError, IndexError, RuntimeError) as error:
                raise error.__new__(error.__class__, f"{type(error).__name__} in the constraint with the following values: {constraint} and Attributes: {[args.to_dict() for args in args_type]}\n{type(error).__name__}: " + str(error))

    def __parse_function_value(self, value: str, attr_type: DeclareFunctions.DeclAttributeType) -> (str, str, str, str):
        """
        Parses the values of the arguments of a function. Arguments can be integers, floats, user variables or strings of already encoded values.
        To the following arguments a conditional condition can be appended at the start of the string or at the end of the string
        Examples of variables:
            Integers: Any positive integer value
            Conditional Integers: Any positive integer value followed or preceded by one of the following conditional conditions: ==, !=, <=, >=, <, > Ex: <=10 or 20>=
            Floats: Any floats value. Floats are defined using the point and not the comma
            Conditional Floats: Any Floats value followed or preceded by one of the following conditional conditions: ==, !=, <=, >=, <, > Ex: <= 10.9 or 14.32==
            User Variables: Any user variable. User variable are declared with :followed by uppercase text.
            Strings: Any string value. Strings are declare elements defined in the activity phase, bind phase or attribute phase. If These strings are not defined then an error is raised.
        """

        # Checks if the original value is empty and returns it in case it is
        if attr_type.can_be_empty and value == "_":
            return value, value, "", ""

        # First checks if the value can have a  conditional operator in front or at the end
        # If it has the operator, it is stored for later since it will be used for creating the additional ASP constraint
        op = None
        # Defines if the operator is found at the start or at the end
        op_at_start: bool = False

        # If the operators are allowed then
        if attr_type.can_have_op:
            # Search for operator presence
            for operator in DeclareFunctions.DECL_CONDITIONAL_OPERATORS:
                # If the value is found the operator is removed from the string and the loop will be aborted
                if value.startswith(operator) or value.endswith(operator):
                    op_at_start = value.startswith(operator)
                    value = value.replace(operator, "")
                    op = operator
                    break

        # The value and the encoded values are then calculated using parsing
        value, encoded_value = self.__parse_variable_value(value, attr_type.decl_type)

        # At this point if the conditional operator was not found then the function does not have additional constraints
        if op is None:
            return value, encoded_value, "", ""

        # Otherwise it has additional constraints and then those must be parsed
        else:
            # A new variable is created
            var = self.__generate_new_variable_name()
            # Based on where the conditional operator was, the constraint is created
            # Ex: function(>=10) becomes function(VAR), VAR>=10 or  function(10>=) becomes function(VAR), 10>=VAR
            if op_at_start:
                return var, var, var + " " + op + " " + value, var + " " + op + " " + encoded_value
            else:
                return var, var, value + " " + op + " " + var, encoded_value + " " + op + " " + var

    def __parse_conditional_constraint(self, values: typing.List[str]) -> (str, str):
        """
        Parses the conditional declare constraints defined by the user.
        Ex: :Var1 >= 10 or :Var2 < :Var3 or :Var4 == AA, :Var5 != :Var6 etc ...
        EX: :Var1 + 5 >= 10 or :Var2 < :Var3 - 10 or :Var4 == 10 - :Var5, etc ...
        """

        if len(values) != 3 and len(values) != 5 and len(values) != 7:
            raise RuntimeError(f"Something during the parsing phase went wrong. Conditional constraints elements must be 3, 5 or 7. Found {len(values)} elements {values}")

        # Creates the 2 lists that will contain our conditional constraint (encoded and not)
        conditional_constraint = []
        encoded_conditional_constraint = []

        # For each element, value and operations are alternated: var, op, var, op, var, op, var
        for index, value in enumerate(values):
            # We have a variable
            if index % 2 == 0:
                var, enc_var = self.__parse_variable_value(value)
                conditional_constraint.append(var)
                encoded_conditional_constraint.append(enc_var)
            # We have an operation
            else:
                conditional_constraint.append(value)
                encoded_conditional_constraint.append(value)

        # Return a string of the not encoded constraints and another string of the encoded constraints both joined by spaces
        return " ".join(conditional_constraint), " ".join(encoded_conditional_constraint)

    def __parse_variable_value(self, value: str, value_type: str = DeclareFunctions.DECL_ANY_ARG) -> (str, str):
        """
        Parses the value of a variable. Values can be Variables, Integers, Floats or constants
        """

        # Checks if the value is a variable
        if value.startswith(":"):
            value = encoded_value = value[1:].upper()
            self.__user_variable_list.append(value)

        # Parses to int the value if it expects an int or floats or any
        elif value_type == DeclareFunctions.DECL_INT_OR_FLOAT_ARG or value_type == DeclareFunctions.DECL_ANY_ARG:
            try:
                # Tries to parse the value by checking if it is a float or an int
                # If it doesn't contain a . then it is not a float and parses to int otherwise parses to float
                # If any exception is raised during the operations then it is a value, and it is returned encoded and non
                if value.find(".") == -1:
                    value, encoded_value = self.__parse_int(value)
                else:
                    value, encoded_value = self.__parse_float(value)
            except ValueError as er:
                # If an exception is raised encode the value if the type is any
                # Raises an exception if the value was not encoded before.
                # If this happens the value that the program wants to encode was not declared in the model and hence does not exist
                if value_type == DeclareFunctions.DECL_ANY_ARG:
                    encoded_value = Encoder().encode_value(value)
                    # encoded_value = Encoder().create_and_encode_value(value)
                # Otherwise raise the exception
                else:
                    raise er
        # Parses to int the value if it expects an int
        elif value_type == DeclareFunctions.DECL_INT_ARG:
            value, encoded_value = self.__parse_int(value)

        # Parses to float the value if it expects a float
        elif value_type == DeclareFunctions.DECL_FLOAT_ARG:
            value, encoded_value = self.__parse_float(value)

        # Encodes directly the value if it is a declare element
        elif value_type == DeclareFunctions.DECL_ENCODE_ARG:
            # Raises an exception if the value was not encoded before. If this happens the value that the program wants to encode was not declared in the model and hence does not exist
            encoded_value = Encoder().encode_value(value)
            # encoded_value = Encoder().create_and_encode_value(value)

        else:
            raise RuntimeError(f"Unrecognized value type: {value_type}")

        # Returns the value and its encoding value
        return value, encoded_value

    @staticmethod
    def __parse_int(value: str) -> (str, str):
        """
        Parses a string to integer.
        Will raise an error if the value is not an integer or positive.

        Returns the normal value followed by the encoded value. (which is the same in this case)
        """
        if int(value) < 0:
            raise ValueError(f"Value {value} must be positive integer")
        value = str(int(value))
        return value, value

    @staticmethod
    def __parse_float(value: str) -> (str, str):
        """
        Parses a string to float and applies the precision in order to transform the float into a string.
        Will raise an error if the value is not an integer or positive.

        Returns the normal value followed by the encoded value. (which is the same in this case)
        """
        if float(value) < 0:
            raise ValueError(f"Value {value} must be positive float")
        precision = len(value.split(".")[1])
        value = str(int(float(value) * 10 ** precision))
        return value, value

    def __generate_new_variable_name(self) -> str:
        """
        Generates variables names when the user expresses conditional conditions
        """
        variable = self.__name + "V" + str(len(self.__generated_variable_list) + 1)
        self.__generated_variable_list.append(variable)

        return variable

    def __generate_new_rule_name(self) -> str:
        """
        Generates rules names when the user expresses absolute conditions
        """
        rule = (self.__name + "R" + str(len(self.__generated_rule_list) + 1)).lower()
        self.__generated_rule_list.append(rule)

        return rule

    def integrity_check(self):
        """
        Checks if every user variable is used more than 1 time. Variables must be declared and then used.
        It is not correct to insert a variable without then comparing it to something.
        Hence, the presence of a variable in a constraint must be more than 1
        """
        for var, count in Counter(self.__user_variable_list).items():
            if count <= 1:
                raise ValueError(f"Error, variable {var} in constraint: {self.__DECL_constraint} is declared but never used. Variables are used for comparison. More than 1 declaration is required")

    @staticmethod
    def __filter_elements(elements: typing.List[str]) -> typing.List[str]:
        """
        Method used to filter a list of String elements.
        First it is mapped using the method .strip() on each string
        Them is filtered by removing empty strings
        """
        return list(filter(lambda el: len(el) > 0, map(lambda el: el.strip(), elements)))

    def get_name(self) -> str:
        """
        Returns the name of the Constraint
        """
        return self.__name

    def to_asp(self, encode: bool = False) -> str:
        """
        Returns the Constraint as an ASP String. If it is encoded returns the Encoded version
        """
        asp = ""

        if encode:
            rules = self.__encoded_absolute_rules
            constraints = self.__ASP_encoded_constraints
        else:
            rules = self.__absolute_rules
            constraints = self.__ASP_constraints

        for rule in rules:
            asp += rule + ".\n"

        asp += "\n" + ASPFunctions.ASP_CONSTRAINT_RULE + " :- " + ", ".join(constraints) + ".\n"

        return asp

    def to_declare(self) -> str:
        """
        Returns the Constraint as a DECLARE String
        """
        return self.__DECL_constraint

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        """
        Returns the Constraint as a dictionary
        """
        return {
            "Name": self.get_name(),
            "Declare_constraint": self.to_declare(),
            "ASP_constraint": self.to_asp(),
            "Encoded_ASP_constraint": self.to_asp(True)
        }


class PositionalBasedModel(ProcessModel, ASPEntity, DeclareEntity):
    """
    Represents the Positional Based Model. This Entity is created based on The ENTIRE DECLARE MODEL. It can be converted in ASP.
    """

    # Defines constants for time units

    POSITIONAL_TIME_START: int = 1
    POSITIONAL_TIME_END: int = 100

    TIME_UNIT_IN_SECONDS_RANGE_MIN: int = 240
    TIME_UNIT_IN_SECONDS_RANGE_MAX: int = 300

    # Constructor
    def __init__(self,
                 positional_time_start: int = POSITIONAL_TIME_START,
                 positional_time_end: int = POSITIONAL_TIME_END,
                 time_unit_in_seconds_min: int = TIME_UNIT_IN_SECONDS_RANGE_MIN,
                 time_unit_in_seconds_max: int = TIME_UNIT_IN_SECONDS_RANGE_MAX,
                 verbose: bool = False):
        """
        Constructor of the Positional Based Model

        Parameters:
            positional_time_start: int = Minimum ASP time value that events can have
            positional_time_end: int = Maximum ASP time value that events can have
            time_unit_in_seconds_min: int = Minimum value in seconds to which 1 ASP time unit corresponds
            time_unit_in_seconds_max: int = Maximum value in seconds to which 1 ASP time unit corresponds
            verbose: bool = Indicates if the user wants to see debugging information
        """

        super().__init__()

        # Instantiates the debugging variables
        self.__verbose = verbose
        self.__PB_Model_Logger = logging.getLogger("Positional Based Model")

        # Initializes the parsed model as empty
        self.__parsed_model: str = ""

        # Initializes the Dictionaries of Activities, Attributes and Constraints
        # Also creates a special list for precision type attributes for later parsing purposes
        self.__activities: typing.Dict[str, Activity] = {}
        self.__attributes: typing.Dict[str, Attribute] = {}
        self.__precision_attributes: typing.Dict[str, Attribute] = {}
        self.__constraints: typing.List[PBConstraint] = []

        # Sets the range of time in which the ASP model will operate and the time unit and second ratio
        self.__positional_based_time_range: typing.Union[(int, int), None] = None
        self.set_positional_based_time_range(positional_time_start, positional_time_end)
        self.__time_unit_in_seconds_range: typing.Union[(int, int), None] = None
        self.set_time_unit_in_seconds_range(time_unit_in_seconds_min, time_unit_in_seconds_max)

    def parse_from_file(self, model_path: str, **kwargs) -> typing_extensions.Self:
        """
        Given a model path it reads the DECLARE MODEL file in the path and parses each line of the model
        """

        # Checks for some errors in the variables
        if model_path is None:
            raise ValueError("Model path cannot be None")
        if not isinstance(model_path, str):
            raise ValueError(f"Model path should be a string, and is instead {type(model_path)}")

        # Opens the files, and reads the whole content
        with open(model_path, "r+") as model_file:
            content = model_file.read()

        # Sends the content to the parsing and returns itself as an object
        return self.parse_from_string(content)

    def parse_from_string(self, content: str, **kwargs) -> typing_extensions.Self:
        """
        Given a DECLARE MODEL String parses the String into a Positional Based Model
        """

        # Checks for some errors in the variables
        if content is None:
            raise ValueError("Model content cannot be None")
        if not isinstance(content, str):
            raise ValueError(f"Model should be a string, and is instead {type(content)}")

        # For each line in the model try to parse the line, Otherwise catch errors and raises them with the line of the model. For better debugging purposes :)
        for index, line in enumerate(content.split('\n')):
            try:
                # If the line is not a comment or empty
                if not DeclareFunctions.is_comment_line(line):
                    # Parse the line
                    self.__debug_message(f"Parsing line {index + 1} of model: {line}")
                    self.__parse_line(line)
            except (ValueError, IndexError, RuntimeError) as error:
                raise error.__new__(error.__class__, f"Line {index + 1} of model: " + str(error))

        # Once the whole model is parsed then an Integrity check is done
        self.__integrity_check()
        # The precision attributes are collected
        self.__set_precision_attributes()
        # The parsed model is stored
        self.__parsed_model = content

        # Returns itself asa Positional Based Model obj
        return self

    def __parse_line(self, line: str):
        """
        Parse a line of the model
        """

        # Splits and joins the string with more spaces into single spaces
        line = " ".join(line.split())

        # If the line is an activity line
        if DeclareFunctions.is_activation_line(line):

            # The activities are extracted
            activities: typing.List[str] = DeclareFunctions.parse_activation_line(line)

            # For each activity an Activity object is created
            for activity_name in activities:
                self.__debug_message(f"Defining new activity: {activity_name}")
                self.__set_activity(activity_name)

        # If the line is a bind line
        elif DeclareFunctions.is_bind_line(line):

            # The activities and the attributes are extracted from the line
            activities, attributes = DeclareFunctions.parse_bind_line(line)
            self.__debug_message(f"Assigning to the following activities: {activities} the following attributes: {attributes}")

            # For each activity
            for activity_name in activities:

                # If the activity does not exist create such activity
                if activity_name not in self.__activities:
                    warnings.warn(f"Activity {activity_name} was not defined before using an activity definition line. The activity will be defined automatically. Check if this is intentional")
                    self.__set_activity(activity_name)

                # Add each Attribute to the current activity
                for attribute_name in attributes:
                    self.__set_attribute(attribute_name, self.__activities[activity_name])

        # If the line is an attribute definition line
        elif DeclareFunctions.is_attribute_line(line):

            # Then the attributes, the type of every attribute and the values are extracted from the line
            attributes, attribute_type, attribute_values = DeclareFunctions.parse_attribute_line(line)
            self.__debug_message(f"Assigning to the following attributes: {attributes} the following values: {attribute_values} of type '{attribute_type}'")

            # For each attribute extracted
            for attribute_name in attributes:

                # Add the attribute to the attribute dictionary if not present
                if attribute_name not in self.__attributes.keys():
                    self.__set_attribute(attribute_name)

                # Parse the attribute values into the Attribute object
                self.__attributes[attribute_name].parse_values(attribute_type, attribute_values)

        # If the line is a Constraint line
        elif DeclareFunctions.has_constraints_in_line(line):
            # A new constraint will be created and appended to the constraints list
            self.__constraints.append(PBConstraint(str(len(self.__constraints) + 1), self.__attributes, line))

        # If the line wasn't recognized is then skipped
        else:
            self.__debug_message(f"Skipping Line, reason: could not recognize the line value: {line}")

    def __set_attribute(self, attribute_name: str = "", activity: typing.Union[Activity, None] = None):
        """
        Given an Attribute and an Activity, store the Attribute in the Attributes list and set the attribute to the activity if one activity was given
        """
        # If the attribute is not in the list of attributes of the model add it to the list
        if attribute_name not in self.__attributes.keys():
            self.__attributes[attribute_name] = Attribute(attribute_name)

        # If there isn't an Activity return
        if activity is None:
            return

        # If the attribute is not in the list of attributes of the activity add it to the list
        if attribute_name not in activity.get_attributes().keys():
            activity.set_attribute(self.__attributes[attribute_name])

    def __set_precision_attributes(self):
        """
        Stores each float attribute in a special dictionary for later precision parsing purposes
        """
        for attribute_name, attribute in self.__attributes.items():
            if attribute.get_type() == Attribute.FLOAT_RANGE:
                self.__precision_attributes[attribute_name] = attribute

    def __set_activity(self, activity_name: str):
        """
        Given an activity name creates an Activity Object and adds the Activity in the activities dictionary
        """

        # Activity name cannot contain the character sequence ': ' otherwise an error will be raised
        if activity_name.find(": ") != -1:
            raise ValueError(f"Activity {activity_name} cannot contain the sequence of characters ': ' ")

        # If the activity is not defined, define the activity
        if activity_name in self.__activities.keys():
            self.__debug_message(f"Activity {activity_name} is already defined, skipped")
        else:
            self.__activities[activity_name] = Activity(activity_name)

    def __integrity_check(self):
        """
        Checks the integrity of the model in order to find errors in the attribute declaration or in the constraint declaration
        """

        attributes_to_remove = []
        # For every attribute
        for attribute in self.__attributes.values():
            # If the type is None then the attribute was declared in the DECLARE model but never initialized. An error will be then launched
            if attribute.get_type() is None:
                raise ValueError(f"Attribute {attribute.get_name()} is not initialized")

            # If the Attribute was declared but never used is then removed
            found = False
            for activity in self.__activities.values():
                if attribute.get_name() in activity.get_attributes().keys():
                    found = True
                    break

            # If it was not found in any activity it is set to be removed
            if not found:
                self.__debug_message(f"Attribute {attribute.get_name()} is not assigned to any activity, removing attribute from model")
                attributes_to_remove.append(attribute.get_name())

        # Any non used Attributes is then removed
        for attribute_to_remove in attributes_to_remove:
            self.__attributes.pop(attribute_to_remove)

        # Each constraint is checked in order to see if the user variables declare are also used
        for constraint in self.__constraints:
            constraint.integrity_check()

    def apply_precision(self, attribute_name: str, value: int):
        """
        Given an Attribute name and a value if the attribute is a float then the integer value is parsed into a float.
        Otherwise, the value is returned
        """
        if attribute_name in self.__precision_attributes.keys():
            return self.__precision_attributes[attribute_name].apply_precision(value)
        return value

    def to_file(self, model_path: str, asp_file: bool = True, encode: bool = False, negative_traces: bool = False, decl_file: bool = True, parsed_model: bool = False):
        """
        Exports the current model to ASP and Declare.
        If the variable asp_file is true then the path is passed to the correct method with its connected variables
        If the variable decl_file is true then the path is passed to the correct method with its connected variables

        Parameters
            model_path: Path in which the file will be created
            asp_file: bool, default True, creates the asp file
            encode: bool, default True, creates the ASP encoded file
            negative_traces: bool, default False, creates the ASP negative traces file
            decl_file: bool, default True, creates the Declare file
            parsed_model: bool, default False, returns the Declare parsed model and creates a file with it
        """
        if asp_file:
            self.to_asp_file(model_path, encode, negative_traces)
        if decl_file:
            self.to_decl_file(model_path, parsed_model)

    def to_asp_file(self, model_path: str, encode: bool = False, negative_traces: bool = False):
        """
        Exports the current model to ASP

        Parameters
            model_path: Path in which the file will be created
            asp_file: bool, default True, creates the asp file
            encode: bool, default True, creates the ASP encoded file
            negative_traces: bool, default False, creates the ASP negative traces file
        """
        self.__export_file(model_path, self.to_asp(encode, negative_traces), ASPFunctions.ASP_FILE_EXTENSION)

    def to_asp_file_without_constraints(self, model_path: str, encode: bool = False):
        """
        Exports the current model to ASP without constraints

        Parameters
            model_path: Path in which the file will be created
            asp_file: bool, default True, creates the asp file
            encode: bool, default True, creates the ASP encoded file
        """
        self.__export_file(model_path, self.to_asp_without_constraints(encode), ASPFunctions.ASP_FILE_EXTENSION)

    def to_one_asp_file_per_constraints(self, model_path: str, encode: bool = False, generate_also_negatives: bool = False):
        """
        Exports the current model to ASP for each constraint

        Parameters
            model_path: Path in which the file will be created
            asp_file: bool, default True, creates the asp file
            encode: bool, default True, creates the ASP encoded file
            negative_traces: bool, default False, creates the ASP negative traces file
        """
        # Removes the file extension
        if model_path.endswith(".lp"):
            model_path = model_path[:-3]

        # Generate files for each positive constraint
        asp_models = self.to_asp_with_single_constraints(encode)

        if len(asp_models) > 0:
            for index, asp in enumerate(asp_models):
                self.__export_file(model_path + f"_pos_const_{index}", asp, ASPFunctions.ASP_FILE_EXTENSION)

        # Generate files for each negative constraint
        if generate_also_negatives:

            asp_models = self.to_asp_with_single_constraints(encode, True)

            if len(asp_models) > 0:
                for index, asp in enumerate(asp_models):
                    self.__export_file(model_path + f"_neg_const_{index}", asp, ASPFunctions.ASP_FILE_EXTENSION)

    def to_decl_file(self, model_path: str, parsed_model: bool = False):
        """
        Exports the current model to Declare

        Parameters
            decl_file: bool, default True, creates the Declare file
            parsed_model: bool, default False, returns the Declare parsed model and creates a file with it
        """
        declare: str = self.__parsed_model if parsed_model else self.to_declare()
        self.__export_file(model_path, declare, DeclareFunctions.DECL_FILE_EXTENSION)

    @staticmethod
    def __export_file(model_path: str, content: str, extension: str):
        """
        Given a path, a content and an extension, writes the content to a file
        """

        # Checks for some problems with the variables
        if model_path is None:
            raise ValueError("Model path cannot be None")
        if not isinstance(model_path, str):
            raise ValueError(f"Model path should be a string, and is instead {type(model_path)}")

        # Extends the path if it does not end with the extension
        if not model_path.endswith(extension):
            model_path += extension

        # If the content is not empty exports the content into a file
        if len(content) != 0:
            with open(model_path, "w+") as model_file:
                model_file.write(content)
        # Otherwise a warning will be raised
        else:
            warnings.warn(f"The model is empty, hence the file will not be created")

    def to_asp(self, encode: bool = False, generate_negatives: bool = False) -> str:
        """
        Returns the model as an ASP String.
        If it is encoded returns the Encoded version
        If it is generate_negatives inverts the ASP condition in order to generate traces that do not match the constraints
        """

        # Generates the ASP strings for the activities and attributes together with the ASP encoding
        asp = self.to_asp_without_constraints(encode)

        # Appends to the String each constraint if there are
        if len(self.__constraints) > 0:
            for constraint in self.__constraints:
                asp += constraint.to_asp(encode) + "\n"

            # Decides which rule to append in order to generate positives or negatives traces
            if generate_negatives:
                asp += ":- " + ASPFunctions.ASP_CONSTRAINT_RULE + ".\n"
            else:
                asp += ":- not " + ASPFunctions.ASP_CONSTRAINT_RULE + ".\n"

        # Returns the ASP String
        return asp

    def to_asp_without_constraints(self, encode: bool = False) -> str:
        """
        Returns the model as an ASP String without constrains attached.
        """

        # Appends the time range rule together with the ASP ENCODING
        asp = ASPFunctions.ASP_TIME_RANGE_FORMAT.format(self.__positional_based_time_range[0], self.__positional_based_time_range[1]) + "\n"
        asp += ASPFunctions.ASP_ENCODING + "\n\n"

        # Appends to the String each activity to ASP
        for activity in self.__activities.values():
            asp += activity.to_asp(encode) + "\n"

        # Appends to the String each attributes to ASP
        for attribute in self.__attributes.values():
            asp += attribute.to_asp(encode) + "\n"

        # Returns the ASP String
        return asp

    def to_asp_with_single_constraints(self, encode: bool = False, generate_negatives: bool = False) -> typing.List[str]:
        """
        Returns a list of the ASP model as a String but each model has a different constraint
        """

        # Generates the ASP without constraints
        asp = self.to_asp_without_constraints(encode)

        # If no constraints are found then the current ASP model is returned
        if len(self.__constraints) == 0:
            warnings.warn("The model does not have constraints, using unconstrained model")
            return []

        # Otherwise a list is created and for each constraint a different ASP encoding string of the model is created
        asp_list: typing.List[str] = []

        for constraint in self.__constraints:
            # Append the constraint
            asp_cost = constraint.to_asp(encode) + "\n"
            # Decide if the traces must be positive or negative
            if generate_negatives:
                asp_cost += ":- " + ASPFunctions.ASP_CONSTRAINT_RULE + ".\n"
            else:
                asp_cost += ":- not " + ASPFunctions.ASP_CONSTRAINT_RULE + ".\n"
            # Append the ASP
            asp_list.append(asp + asp_cost)

        # Return the ASP List
        return asp_list

    def to_declare(self) -> str:

        """
        Parses the current model to declare
        """

        decl = ""

        # Parses to declare every activity
        for activity in self.__activities.values():
            decl += activity.to_declare() + "\n"

        # Parses to declare every attribute
        for attribute in self.__attributes.values():
            decl += attribute.to_declare() + "\n"

        # Parses to declare every constraint
        for constraint in self.__constraints:
            decl += constraint.to_declare() + "\n"

        # Returns the declare model
        return decl

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        """
        Returns the model as a dictionary
        """

        return {
            "activities": [act.to_dict(False) for act in self.__activities.values()],
            "attributes": [attr.to_dict() for attr in self.__attributes.values()],
            "constraints": [constr.to_dict() for constr in self.__constraints]
        }

    def get_activity_dict(self) -> typing.Dict[str, Activity]:
        """
        Returns the activities list of the model
        """
        return self.__activities

    def get_attributes_dict(self) -> typing.Dict[str, Attribute]:
        """
        Returns the attributes list of the model
        """
        return self.__attributes

    def get_constraints_list(self) -> typing.List[PBConstraint]:
        """
        Returns the constraints list of the model
        """
        return self.__constraints

    def get_parsed_model(self) -> str:
        """
        Returns the parsed model given as an input
        """
        return self.__parsed_model

    def set_positional_based_time_range(self, positional_time_start: int = POSITIONAL_TIME_START, positional_time_end: int = POSITIONAL_TIME_END):
        """
        Sets the positional based time range of the model
        """
        self.__positional_based_time_range = tuple(self.__set_and_check_range("Positional Based Time Range", positional_time_start, positional_time_end))

    def set_time_unit_in_seconds_range(self, time_unit_in_seconds_min: int = TIME_UNIT_IN_SECONDS_RANGE_MIN, time_unit_in_seconds_max: int = TIME_UNIT_IN_SECONDS_RANGE_MAX):
        """
        Sets the time unit in seconds range of the model
        """
        self.__time_unit_in_seconds_range = tuple(self.__set_and_check_range("Time Unit in Seconds Range", time_unit_in_seconds_min, time_unit_in_seconds_max))

    @staticmethod
    def __set_and_check_range(name: str, start_or_min: int, end_or_max: int):
        """
        Sets the range of time in which the traces will be generated
        """

        # Checks for non integer instances
        if not isinstance(start_or_min, int) or not isinstance(end_or_max, int):
            raise TypeError(f"{name} values must be an integer")

        # Checking negative values
        if start_or_min <= 0:
            start_or_min = abs(start_or_min)
            warnings.warn(f"{name} min or start must be greater than zero. Applying absolute value")
        if end_or_max <= 0:
            end_or_max = abs(end_or_max)
            warnings.warn(f"{name} max or end must be greater than zero. Applying absolute value")

        # Invert values if the start is bigger than the end
        if start_or_min > end_or_max:
            start_or_min, end_or_max = end_or_max, start_or_min

        # Sets the range
        return start_or_min, end_or_max

    def get_time_unit_in_seconds_range(self) -> (int, int):
        """
        Returns the time unit in seconds conversion
        """
        return self.__time_unit_in_seconds_range

    def set_verbose(self, verbose: bool = False):
        """
        Sets verbose for debugging information
        """
        self.__verbose = verbose

    def __debug_message(self, message: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """
        if self.__verbose:
            self.__PB_Model_Logger.debug(str(message))


if __name__ == "__main__":
    """
    constraint_value1 = "payload_range(valore, 200, 300, 6), payload_range(valore, 200, 300, _) ,pos(ER Registration, >= 1, ==10), absolute_payload(age, 30), absolute_pos(ER Registration, 2, _), absolute_pos(ER Registration, 3, 10), pos(ER Registration, 1, 10), payload(org:group, !=1, :V1), :V1 <= aA"
    constraint_value2 = "payload_range(valore, 200, 300, 6)"
    const: PBConstraint = PBConstraint("1", constraint_value2)
    print(const.to_declare())
    print(const.to_asp())
    print(const.to_asp(True))
    """
    """
    # const: PBConstraint = PBConstraint("1", "pos(ER Registration, >= 1, ==10), payload(org:group, !=1, :V1), !pos(!=ER Sepsis Triage, 2, <=30), !payload(org:group, 2.00 <=, :V2), :V1 == aA, 1 == :V2") pos(:V2, 1, 1), pos(ER Triage, 2, 4), payload(:V1, B, 1), payload(:V1, F, 2)
    const: PBConstraint = PBConstraint("1", "pos(1, 2, 10), pos(:V1, 1, 10), pos(!= ER Registration, 1, 10), pos(ER Registration, >= 1, 10  ==), pos(:V1, >1, 10<), pos(!=ER Registration, <1, !=10)")
    print(const.to_declare())
    print(const.to_asp())
    print(const.to_asp(True))
    const: PBConstraint = PBConstraint("1", "pos(!=:V1, >:V2, :V3)")
    print(const.to_declare())
    print(const.to_asp())
    print(const.to_asp(True))
    """

    # model1 = PositionalBasedModel(True).parse_from_file("DeclareFiles/payload_range_test.decl")
    # model1.to_asp_file("ASPFiles/payload_range_test.lp")

    # model2 = PositionalBasedModel(True).parse_from_file("model_simplified.decl")
    # model2 = PositionalBasedModel(True).parse_from_file("model_simplified.decl").to_asp()

    # model1.to_decl_file("ASPFiles/model_test1.decl")

    """
    atr, types, vals = DeclareFunctions.parse_attribute_line("a,v,b,d,s: float between")
    attribute = Attribute("name")
    attribute.parse_values(types, vals)
    print(attribute.get_type())
    print(attribute.get_values())
    print(attribute.get_precision())
    """

    pass
