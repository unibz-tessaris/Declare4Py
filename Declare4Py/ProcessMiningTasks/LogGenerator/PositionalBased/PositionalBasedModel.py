import typing
import typing_extensions
import logging
import re

from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.ASPUtils import ASPFunctions, ASPEntity
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.DeclareUtils import DeclareFunctions, DeclareEntity
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.PBEncoder import Encoder


class Attribute(ASPEntity, DeclareEntity):
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    def __init__(self, name):
        self.__name: str = name
        self.__type: typing.Union[str, None] = None
        self.__values: typing.List = []
        self.__precision: int = 0

    def parse_values(self, values: str):

        self.__values = []
        self.__precision = 0

        values = values.strip()

        if values.lower().find(DeclareFunctions.DECL_FLOAT_BETWEEN) != -1:
            self.__type = Attribute.FLOAT_RANGE
            float_range = values.lower().replace(DeclareFunctions.DECL_FLOAT_BETWEEN, "").strip().split(" and ")
            min_float: float = float(float_range[0])
            max_float: float = float(float_range[1])

            while True:

                min_float *= 10
                max_float *= 10

                self.__precision += 1

                if min_float == int(min_float) and max_float == int(max_float):
                    break

            self.__values.append(int(min_float))
            self.__values.append(int(max_float))

        elif values.lower().find(DeclareFunctions.DECL_INTEGER_BETWEEN) != -1:
            self.__type = Attribute.INTEGER_RANGE
            int_range = values.lower().replace(DeclareFunctions.DECL_INTEGER_BETWEEN, "").strip().split(" and ")
            self.__values.append(int(int_range[0]))
            self.__values.append(int(int_range[1]))

        else:
            self.__type = Attribute.ENUMERATION
            self.__values = "".join(values.split()).split(",")

    def get_name(self) -> str:
        return self.__name

    def get_encoded_name(self) -> str:
        return Encoder().encode_value("ATTRIBUTES", self.__name)

    def get_type(self) -> typing.Union[str, None]:
        return self.__type

    def get_values(self) -> typing.Union[typing.List[int], typing.List[str]]:
        return self.__values

    def get_encoded_values(self) -> str:
        return Encoder().encode_values("ATTR_VALUES", self.__values)

    def get_precision(self) -> int:
        return self.__precision

    def apply_precision(self, value: int) -> float:
        return value / 10 ** self.__precision

    def to_asp(self, encoded: bool = False) -> str:
        asp = ""

        if encoded:
            name = self.get_encoded_name()
            values = self.get_encoded_values()
        else:
            name = self.get_name()
            values = self.get_values()

        if self.__type == Attribute.ENUMERATION:
            for value in values:
                asp += ASPFunctions.ASP_ATTRIBUTE_VALUE.format(name, value) + ".\n"
        else:
            asp = ASPFunctions.ASP_ATTRIBUTE_RANGE.format(name, self.__values[0], self.__values[1]) + ".\n"

        return asp

    def to_declare(self) -> str:
        decl = self.__name + ": "

        if self.__type == Attribute.INTEGER_RANGE:
            decl += DeclareFunctions.DECL_INTEGER_BETWEEN + " " + str(self.__values[0]) + " and " + str(self.__values[1])
        elif self.__type == Attribute.FLOAT_RANGE:
            decl += DeclareFunctions.DECL_FLOAT_BETWEEN + " " + str(self.__values[0] / 10 ** self.__precision) + " and " + str(self.__values[1] / 10 ** self.__precision)
        else:
            decl += ", ".join(self.__values)

        return decl

    def to_dict(self) -> typing.Dict[str, typing.Any]:

        values = "values" if self.get_type() == Attribute.ENUMERATION else "range"

        attr_dict = {
            "name": self.get_name(),
            "type": self.get_type(),
            values: self.get_values()
        }

        if self.get_type() == Attribute.FLOAT_RANGE:
            attr_dict["precision"] = self.get_precision()

        return attr_dict


class Activity(ASPEntity, DeclareEntity):

    def __init__(self, name: str):

        self.__name = name
        self.__attributes: typing.Dict[str, Attribute] = {}

    def get_name(self) -> str:
        return self.__name

    def get_encoded_name(self) -> str:
        return Encoder().encode_value("ACTIVITIES", self.__name)

    def get_attributes(self) -> typing.Dict[str, Attribute]:
        return self.__attributes

    def get_encoded_attributes(self) -> typing.List[str]:
        return Encoder().encode_values("ATTRIBUTES", list(self.__attributes.keys()))

    def set_attribute(self, attribute: typing.Union[str, Attribute]):
        if isinstance(attribute, str):
            self.__attributes[attribute] = Attribute(attribute)
        elif isinstance(attribute, Attribute):
            self.__attributes[attribute.get_name()] = attribute
        else:
            raise ValueError(f"Attribute {attribute} is not of type str or Attribute but {type(attribute)}")

    def to_asp(self, encoded: bool = False) -> str:

        if encoded:
            name = self.get_encoded_name()
            attributes = self.get_encoded_attributes()
        else:
            name = self.get_name()
            attributes = self.get_attributes().keys()

        asp: str = ASPFunctions.ASP_ACTIVITY.format(name) + ".\n"
        for attribute_name in attributes:
            asp += ASPFunctions.ASP_HAS_ATTRIBUTE.format(name, attribute_name) + ".\n"

        return asp

    def to_declare(self) -> str:

        decl = DeclareFunctions.DECL_ACTIVITY + " " + self.__name + "\n"
        decl += DeclareFunctions.DECL_BIND + " " + self.__name + ": " + ", ".join(self.__attributes.keys())

        return decl

    def to_dict(self, return_attributes_dict: bool = True) -> typing.Dict[str, typing.Any]:
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

    def __init__(self, name: str, constraint: str):
        self.__name = f"C{name}"
        self.__DECL_constraint: str = constraint
        self.__ASP_constraint: str = ASPFunctions.ASP_CONSTRAINT_RULE + " :- "
        self.__ASP_encoded_constraint = ASPFunctions.ASP_CONSTRAINT_RULE + " :- "
        self.__variable_list: typing.List[str] = []
        self.__parse_constraint(constraint)

    def get_name(self) -> str:
        return self.__name

    def __parse_constraint(self, constraints: str):

        parsed_constraints: typing.List[str] = []
        parsed_encoded_constraints: typing.List[str] = []

        for constraint in "".join(constraints.strip()).split("),"):
            constraint = original_const = constraint.replace("!!", "").strip()

            # Deleting negations and simplifying sequences of negations
            negated: str = ""
            if constraint.startswith("!"):
                constraint = constraint.replace("!", "")
                negated = "not "

            # Parse the function pos or payload
            try:
                if constraint.startswith(DeclareFunctions.DECL_POSITION["function"]) or constraint.startswith(DeclareFunctions.DECL_PAYLOAD["function"]):
                    if constraint.startswith(DeclareFunctions.DECL_POSITION["function"]):
                        const, encoded_const = self.__parse_constraint_function(constraint, "ACTIVITIES", ASPFunctions.ASP_EVENT["function"], ASPFunctions.ASP_EVENT["attr_count"], DeclareFunctions.DECL_POSITION["function"], DeclareFunctions.DECL_POSITION["attr_count"])
                    else:
                        const, encoded_const = self.__parse_constraint_function(constraint, "ATTRIBUTES", ASPFunctions.ASP_ASSIGNED_VALUE["function"], ASPFunctions.ASP_ASSIGNED_VALUE["attr_count"], DeclareFunctions.DECL_PAYLOAD["function"], DeclareFunctions.DECL_PAYLOAD["attr_count"])
                    parsed_constraints.append(negated + const)
                    parsed_encoded_constraints.append(negated + encoded_const)
                    continue
            except ValueError as error:
                raise ValueError(str(error) + f", Original constraint: {original_const}")

            if re.match(r"(\w+\s+(==|=|>|<|>=|<=)\s+\w+(,\s)*)+", constraint):
                parsed_constraints.append(constraint)
                parsed_encoded_constraints.append(constraint)
                continue

            raise ValueError(f"Cannot parse the constraint with value: {original_const}")

        self.__ASP_constraint += ", ".join(parsed_constraints) + "."
        self.__ASP_encoded_constraint += ", ".join(parsed_encoded_constraints) + "."

    def __parse_constraint_function(self, constraint: str, target_type: str, asp_function: str, asp_attr: int, decl_function: str,  decl_attr: int) -> typing.Tuple[str, str]:

        if asp_attr != decl_attr or asp_attr <= 0 or decl_attr <= 0:
            raise RuntimeError(f"Attributes count of functions {asp_function} with {asp_attr} and of functions {decl_function} with {decl_attr} are not equal or are <= 0")

        values = constraint.replace(decl_function + "(", "").replace(")", "").split(",")

        if len(values) != decl_attr:
            raise ValueError(f"Constraint {decl_function} requires {decl_attr} values")

        format_list: typing.List[str] = [values[0].strip()]
        extra_conditions: str = ""

        encoded_format_list: typing.List[str] = [Encoder().encode_value(target_type, values[0])]
        encoded_extra_conditions: str = ""

        attr: int = 1
        while attr < len(values):

            try:
                format_list.append(str(int(values[attr])))
                encoded_format_list.append(str(int(values[attr])))
            except ValueError:

                attribute_value = values[attr].strip()
                if attribute_value.startswith(":"):
                    attribute_value = encoded_attribute_value = attribute_value.replace(":", "")
                else:
                    attribute = attribute_value.replace("!", "").replace("<", "").replace(">", "").replace("=", "")
                    try:
                        int(attribute)
                        encoded_attribute_value = attribute_value
                    except ValueError:
                        encoded_attribute_value = attribute_value.replace(attribute, Encoder().encode_value("ATTR_VALUES", attribute))

                variable = self.__generate_new_variable_name()

                if attribute_value.startswith("!"):
                    extra_conditions = variable + attribute_value.replace("!", "!=")
                    encoded_extra_conditions = variable + encoded_attribute_value.replace("!", "!=")
                elif attribute_value.startswith(">") or attribute_value.startswith(">=") or attribute_value.startswith("<") or attribute_value.startswith("<="):
                    extra_conditions = variable + attribute_value
                    encoded_extra_conditions = variable + encoded_attribute_value
                elif attribute_value.endswith(">") or attribute_value.endswith(">=") or attribute_value.endswith("<") or attribute_value.endswith("<="):
                    extra_conditions = attribute_value + variable
                    encoded_extra_conditions = encoded_attribute_value + variable
                else:
                    variable = attribute_value

                format_list.append(variable)
                encoded_format_list.append(variable)
            attr += 1

        asp = asp_function.format(*format_list)
        encoded_asp = asp_function.format(*encoded_format_list)

        if len(extra_conditions) > 0:
            asp += ", " + extra_conditions
            encoded_asp += ", " + encoded_extra_conditions

        return asp, encoded_asp

    def __generate_new_variable_name(self) -> str:
        count: int = 1
        variable = self.__name + "_V" + str(count)
        while variable in self.__variable_list:
            variable = self.__name + "_V" + str(count)
            count += 1
        self.__variable_list.append(variable)
        return variable

    def to_asp(self, encode: False) -> str:
        if encode:
            return self.__ASP_encoded_constraint
        else:
            return self.__ASP_constraint

    def to_declare(self) -> str:
        return self.__DECL_constraint

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "name": self.get_name(),
            "declare_constraint": self.to_declare()
        }


class PositionalBasedModel(ProcessModel, ASPEntity, DeclareEntity):

    def __init__(self, verbose: bool = False):
        super().__init__()

        self.__verbose = verbose
        self.__PB_Model_Logger = logging.getLogger("Positional Based Model")

        self.__parsed_model: str = ""

        self.__activities: typing.Dict[str, Activity] = {}
        self.__attributes: typing.Dict[str, Attribute] = {}
        self.__precision_attributes: typing.Dict[str, Attribute] = {}
        self.__constraints: typing.List[PBConstraint] = []


    def parse_from_file(self, model_path: str, **kwargs) -> typing_extensions.Self:

        if model_path is None:
            raise ValueError("Model path cannot be None")
        if not isinstance(model_path, str):
            raise ValueError(f"Model path should be a string, and is instead {type(model_path)}")

        with open(model_path, "r+") as model_file:
            content = model_file.read()

        return self.parse_from_string(content)

    def parse_from_string(self, content: str, **kwargs) -> typing_extensions.Self:

        if content is None:
            raise ValueError("Model content cannot be None")
        if not isinstance(content, str):
            raise ValueError(f"Model should be a string, and is instead {type(content)}")

        for index, line in enumerate(content.split('\n')):
            self.__parse_line(index + 1, line)

        self.__integrity_check()
        self.__set_precision_attributes()
        self.__parsed_model = content

        return self

    def __parse_line(self, index: int, line: str):

        line = " ".join(line.split())

        if line.startswith("#") or line == "":
            return

        if line.lower().startswith(DeclareFunctions.DECL_ACTIVITY):
            activities = line.replace(DeclareFunctions.DECL_ACTIVITY, "", 1).split(",")

            for activity_name in activities:
                self.__set_activity(index, activity_name)

        elif line.lower().startswith(DeclareFunctions.DECL_BIND):

            if line.find(": ") == -1:
                raise ValueError(f"Line {index} of model: Could not find the sequence of characters ': ' that divides activities from attributes. EX: act_1, ..., act_n: attr_1, ..., attr_n")

            if len(line.split(": ")) > 2:
                raise ValueError(f"Line {index} of model: The sequence of characters ': ' is present more than 1 time. Cannot distinguish the division of activities and attributes EX: act_1, ..., act_n: attr_1, ..., attr_n")

            activities = line.split(": ", maxsplit=1)[0].replace("bind", "").split(",")
            attributes = line.split(": ", maxsplit=1)[1].split(",")

            for activity_name in activities:
                activity_name = activity_name.strip()

                if activity_name not in self.__activities:
                    self.__debug_message(f"Line {index} of model: Activity {activity_name} is not defined. Defining activity")
                    self.__set_activity(index, activity_name)

                for attribute_name in attributes:
                    self.__set_attribute(attribute_name, self.__activities[activity_name])

        # Define constraint line
        elif DeclareFunctions.line_starts_with_constraint(line):
            try:
                self.__constraints.append(PBConstraint(str(len(self.__constraints) + 1), line))
            except ValueError as error:
                raise ValueError(f"Line {index} of model: " + str(error))

        # The remaining option is that the line does not contain something useful
        # Or it contains an attribute definition line
        else:

            if line.find(": ") == -1:
                self.__debug_message(f"Line {index} of model: Skipping Line, reason: could not recognize the line value: {line}")
                return
            if len(line.split(": ")) > 2:
                raise ValueError(f"Line {index} of model: The sequence of characters ': ' is present more than 1 time. Cannot distinguish the division of attributes and values EX: attr_1, ..., attr_n: val_1, ..., val_n")

            attributes = line.split(": ", maxsplit=1)[0].split(",")
            attribute_values = line.split(": ", maxsplit=1)[1]

            for attribute_name in attributes:
                attribute_name = attribute_name.strip()

                if len(attribute_name) == 0:
                    continue

                if attribute_name not in self.__attributes.keys():
                    self.__set_attribute(attribute_name)

                self.__attributes[attribute_name].parse_values(attribute_values)

    def __set_attribute(self, attribute_name: str = "", activity: typing.Union[Activity, None] = None):

        attribute_name = attribute_name.strip()

        if len(attribute_name) == 0:
            return

        # If the attribute is not in the list of attributes of the model add it to the list
        if attribute_name not in self.__attributes.keys():
            self.__attributes[attribute_name] = Attribute(attribute_name)

        if activity is None:
            return

        # If the attribute is not in the list of attributes of the activity add it to the list
        if attribute_name not in activity.get_attributes().keys():
            activity.set_attribute(self.__attributes[attribute_name])

    def __set_precision_attributes(self):
        for attribute_name, attribute in self.__attributes.items():
            if attribute.get_type() == Attribute.FLOAT_RANGE:
                self.__precision_attributes[attribute_name] = attribute

    def __set_activity(self, index: int, activity_name: str):
        activity_name = activity_name.strip()

        if activity_name.find(": ") != -1:
            raise ValueError(f"Line {index} of model: Activity {activity_name} cannot contain the sequence of characters ': ' ")

        if activity_name in self.__activities.keys():
            self.__debug_message(f"Activity {activity_name} is already defined, skipped")
        else:
            self.__activities[activity_name] = Activity(activity_name)

    def __integrity_check(self):

        attributes_to_remove = []

        for attribute in self.__attributes.values():
            if attribute.get_type() is None:
                raise ValueError(f"Attribute {attribute.get_name()} is not initialized")

            found = False
            for activity in self.__activities.values():
                if attribute.get_name() in activity.get_attributes().keys():
                    found = True
                    break

            if not found:
                self.__debug_message(f"Attribute {attribute.get_name()} is not assigned to any activity, removing attribute from model")
                attributes_to_remove.append(attribute.get_name())

        for attribute_to_remove in attributes_to_remove:
            self.__attributes.pop(attribute_to_remove)

    def apply_precision(self, attribute_name: str, value: int):
        if attribute_name in self.__precision_attributes.keys():
            return self.__precision_attributes[attribute_name].apply_precision(value)
        return value

    def to_file(self, model_path: str, asp_file: bool = True,  encode: bool = False, negative_traces: bool = False, decl_file: bool = True, parsed_model: bool = False):

        if asp_file:
            self.to_asp_file(model_path, encode, negative_traces)
        if decl_file:
            self.to_decl_file(model_path, parsed_model)

    def to_asp_file(self, model_path: str, encode: bool = False, negative_traces: bool = False):
        self.__export_file(model_path, self.to_asp(encode, negative_traces), ASPFunctions.ASP_FILE_EXTENSION)

    def to_decl_file(self, model_path: str, parsed_model: bool = False):
        declare: str = self.__parsed_model if parsed_model else self.to_declare()
        self.__export_file(model_path, declare, DeclareFunctions.DECL_FILE_EXTENSION)

    def __export_file(self, model_path: str, content: str, extension: str):

        if model_path is None:
            raise ValueError("Model path cannot be None")
        if not isinstance(model_path, str):
            raise ValueError(f"Model path should be a string, and is instead {type(model_path)}")

        if not model_path.endswith(extension):
            model_path += extension

        if len(content) != 0:
            with open(model_path, "w+") as model_file:
                model_file.write(content)
        else:
            self.__debug_message(f"The model is empty, hence the file will not be created")

    def to_asp(self, encode: bool = False, generate_negatives: bool = False) -> str:
        asp = ASPFunctions.ASP_ENCODING + "\n\n"

        for activity in self.__activities.values():
            asp += activity.to_asp(encode) + "\n"

        for attribute in self.__attributes.values():
            asp += attribute.to_asp(encode) + "\n"

        for constraint in self.__constraints:
            asp += constraint.to_asp(encode) + "\n"

        if generate_negatives:
            asp += ":- " + ASPFunctions.ASP_CONSTRAINT_RULE + ".\n"
        else:
            asp += ":- not " + ASPFunctions.ASP_CONSTRAINT_RULE + ".\n"

        return asp

    def to_declare(self) -> str:
        decl = ""

        for activity in self.__activities.values():
            decl += activity.to_declare() + "\n"

        for attribute in self.__attributes.values():
            decl += attribute.to_declare() + "\n"

        for constraint in self.__constraints:
            decl += constraint.to_declare() + "\n"

        return decl

    def to_dict(self) -> typing.Dict[str, typing.Any]:

        return {
            "activities": [act.to_dict(False) for act in self.__activities.values()],
            "attributes": [attr.to_dict() for attr in self.__attributes.values()],
            "constraints": [constr.to_dict() for constr in self.__constraints]
        }

    def get_activity_dict(self) -> typing.Dict[str, Activity]:
        return self.__activities

    def get_attributes_dict(self) -> typing.Dict[str, Attribute]:
        return self.__attributes

    def get_constraints_list(self) -> typing.List[PBConstraint]:
        return self.__constraints

    def get_parsed_model(self) -> str:
        return self.__parsed_model

    def set_verbose(self, verbose: bool = False):
        self.__verbose = verbose

    def __debug_message(self, message: any):
        if self.__verbose:
            self.__PB_Model_Logger.debug(str(message))


if __name__ == "__main__":
    model1 = PositionalBasedModel(True).parse_from_file("Declare_Tests/model.decl")
    # model2 = PositionalBasedModel(True).parse_from_file("model_simplified.decl")
    # model2 = PositionalBasedModel(True).parse_from_file("model_simplified.decl").to_asp()
    model1.to_asp_file("asp_enc.lp", True)
    model1.to_asp_file("asp.lp", )
