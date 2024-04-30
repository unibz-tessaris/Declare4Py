import typing
import typing_extensions
from abc import abstractmethod
import logging

from Declare4Py.ProcessModels.AbstractModel import ProcessModel


class ASPEntity:

    ASP_ACTIVITY = "activity({})"
    ASP_HAS_ATTRIBUTE = "has_attribute({}, {})"
    ASP_ATTRIBUTE_VALUE = "attribute_value({}, {})"
    ASP_ATTRIBUTE_RANGE = "attribute_value({}, {}..{})"

    @abstractmethod
    def to_asp(self) -> str:
        pass


class PositionalBasedModel(ProcessModel, ASPEntity):

    def __init__(self, verbose: bool = False):
        super().__init__()

        self.__verbose = verbose
        self.__PB_Model_Logger = logging.getLogger("Positional Based Model")

        self.__model: str = ""

        self.__activities: typing.Dict[str, Activity] = {}
        self.__attributes: typing.Dict[str, Attribute] = {}
        self.__constraints: typing.List[PPMConstraint] = []

    def parse_from_file(self, model_path: str, verbose: bool = False) -> typing_extensions.Self:

        if model_path is None:
            raise ValueError("Model path cannot be None")
        if not isinstance(model_path, str):
            raise ValueError(f"Model path should be a string, and is instead {type(model_path)}")

        with open(model_path, "r+") as model_file:
            for index, line in enumerate(model_file):
                self.__parse_line(index + 1, line)

            self.__integrity_check()
            self.__set_model(str(model_file))

        return self

    def parse_from_string(self, content: str, verbose: bool = False) -> typing_extensions.Self:

        if content is None:
            raise ValueError("Model content cannot be None")
        if not isinstance(content, str):
            raise ValueError(f"Model should be a string, and is instead {type(content)}")

        for index, line in enumerate(content.split('\n')):
            self.__parse_line(index + 1, line)

        self.__integrity_check()
        self.__set_model(content)

        return self

    def __parse_line(self, index: int, line: str):

        line = " ".join(line.split())

        if line.startswith("#") or len(line) == 0:
            return

        if line.startswith("activity"):
            activity_name = line.replace("activity", "", 1).strip()
            if activity_name.find(":") != -1:
                raise ValueError(f"Line {index} of model: Activity name cannot contain the character ':' ")
            self.__activities[activity_name] = Activity(activity_name)

        elif line.startswith("bind"):

            # Dividing the attribute definition line such that ["bind activity_name: attr1", "attr2", etc]
            attribute_def_line = line.split(",")
            # Extracting "bind activity_name: attr1"
            activity_def_name = attribute_def_line[0]
            # Filtering "bind activity_name" -> removing bind -> stripping -> activity_name
            activity_name = activity_def_name[0: activity_def_name.index(":")].replace("bind", "").strip()
            # Taking attr1 out from "bind activity_name: attr1"
            first_attr = activity_def_name[activity_def_name.index(":") + 1:].strip()
            # Checking if the attr is empty: ""
            if len(first_attr) > 0:
                attributes_names = [first_attr] + attribute_def_line[1:]
            else:
                attributes_names = attribute_def_line[1:]

            # Check if activity exists
            if activity_name not in self.__activities.keys():
                raise ValueError(f"Line {index} of model: Activity {activity_name} is not defined and does not exist")

            # Check if at least one attribute is given
            if len(attributes_names) == 0:
                raise ValueError(f"Line {index} of model: Activity {activity_name} should have at least one attribute")

            activity: Activity = self.__activities[activity_name]

            for attribute_name in attributes_names:

                attribute_name = attribute_name.strip()

                # Skip empty values such as ""
                if len(attribute_name) == 0:
                    continue

                # If the attribute is not in the list of attributes of the model add it to the list
                if attribute_name not in self.__attributes.keys():
                    self.__attributes[attribute_name] = Attribute(attribute_name)

                # If the attribute is not in the list of attributes of the activity add it to the list
                if attribute_name not in activity.get_attributes().keys():
                    activity.set_attribute(self.__attributes[attribute_name])

        # Define constraint line
        elif line.startswith("pos") or line.startswith("!pos") or line.startswith("payload") or line.startswith("!payload"):
            self.__constraints.append(PPMConstraint(str(len(self.__constraints) + 1), line))

        # The remaining option is that the line does not contain something useful
        # Or it containts an attribute definition line
        else:

            for attribute_name in self.__attributes.keys():
                
                if line.startswith(attribute_name):
                    attribute_values = line.replace(attribute_name, "").split(":")[1]
                    self.__attributes[attribute_name].parse_values(attribute_values)
                    return

            self.debug_message(f"Line {index} of model: ignored, value: {line}")

    def __integrity_check(self):
        pass

    def to_file(self, model_path: str, **kwargs):

        if model_path is None:
            raise ValueError("Model path cannot be None")
        if not isinstance(model_path, str):
            raise ValueError(f"Model path should be a string, and is instead {type(model_path)}")

        with open(model_path, "w+") as model_file:
            model_file.write(self.__model)

    def to_asp(self) -> str:
        asp = ""

        for activity in self.__activities.values():
            asp += activity.to_asp() + "\n"

        for attribute in self.__attributes.values():
            asp += attribute.to_asp() + "\n"

        for constraint in self.__constraints:
            asp += constraint.to_asp() + "\n"

        return asp

    def to_dict(self) -> typing.Dict[str, typing.Any]:

        activities = []
        attributes = []
        constraints = []

        for activity in self.__activities.values():
            activities.append(activity.to_dict())

        for attribute in self.__attributes.values():
            attributes.append(attribute.to_dict())

        for constraint in self.__constraints:
            constraints.append(constraint.to_dict())

        return {
            "activities": activities,
            "attributes": attributes,
            "constraints": constraints
        }

    def __set_model(self, model: str = ""):
        self.__model = model

    def get_model(self) -> str:
        return self.__model

    def set_verbose(self, verbose: bool = False):
        self.__verbose = verbose

    def debug_message(self, message: any):
        if self.__verbose:
            self.__PB_Model_Logger.debug(str(message))


class Attribute(ASPEntity):

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

        # TODO check if lower make sense
        values = values.lower().strip()

        if values.find("float between") != -1:
            self.__type = Attribute.FLOAT_RANGE
            float_range = values.replace("float between", "").strip().split(" and ")
            min_float: float = float(float_range[0])
            max_float: float = float(float_range[1])

            while min_float != int(min_float) and max != int(max_float):

                min_float *= 10
                max_float *= 10

                self.__precision += 1

            self.__values.append(int(min_float))
            self.__values.append(int(max_float))

            if self.__precision == 0:
                self.__type = Attribute.INTEGER_RANGE

        elif values.find("integer between") != -1:
            self.__type = Attribute.INTEGER_RANGE
            int_range = values.replace("integer between", "").strip().split(" and ")
            self.__values.append(int(int_range[0]))
            self.__values.append(int(int_range[1]))

        else:
            self.__type = Attribute.ENUMERATION
            #TODO check if split() -> join("") -> split(",") + chekc spazi
            self.__values = values.replace(", ",  ",").split(",")

    def get_name(self) -> str:
        return self.__name

    def get_type(self) -> typing.Union[str, None]:
        return self.__type

    def get_values(self) -> typing.Union[typing.List[int], typing.List[str]]:
        return self.__values

    def get_precision(self) -> int:
        return self.__precision

    def to_asp(self) -> str:
        asp = ""

        if self.__type == Attribute.ENUMERATION:
            for value in self.__values:
                asp += Attribute.ASP_ATTRIBUTE_VALUE.format(self.__name, value) + "\n"
        else:
            asp = Attribute.ASP_ATTRIBUTE_RANGE.format(self.__name, self.__values[0], self.__values[1]) + "\n"

        return asp

    def to_dict(self) -> typing.Dict[str, typing.Any]:

        values = "values" if self.get_type() == Attribute.ENUMERATION else "values range"

        attr_dict = {
            "name": self.get_name(),
            "type": self.get_type(),
            values: self.get_values(),
        }

        if self.get_type() == Attribute.FLOAT_RANGE:
            attr_dict["precision"] = self.get_precision()

        return attr_dict


class Activity(ASPEntity):

    def __init__(self, name):

        self.__name = name
        self.__attributes: typing.Dict[str, Attribute] = {}

    def get_attributes(self) -> typing.Dict[str, Attribute]:
        return self.__attributes

    def set_attribute(self, attribute: typing.Union[str, Attribute]):
        if isinstance(attribute, str):
            self.__attributes[attribute] = Attribute(attribute)
        elif isinstance(attribute, Attribute):
            self.__attributes[attribute.get_name()] = attribute
        else:
            raise ValueError(f"Attribute {attribute} is not a str or Attribute but {type(attribute)}")

    def to_asp(self) -> str:

        asp: str = self.ASP_ACTIVITY.format(self.__name) + "\n"
        for attribute_name in self.__attributes.keys():
            asp += self.ASP_HAS_ATTRIBUTE.format(self.__name, attribute_name) + "\n"
        return asp

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "name": self.__name,
            "attributes": list(self.__attributes.keys())
        }


class PPMConstraint(ASPEntity):

    def __init__(self, name: str, constraint: str):
        self.__name = f"constraint_{name}"
        self.__constraint: str = constraint

    def get_name(self) -> str:
        return self.__name

    def get_constraint(self) -> str:
        return self.__constraint

    def to_asp(self) -> str:
        return self.__constraint

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "name": self.get_name(),
            "constraint": self.get_constraint()
        }


from pprint import pprint
if __name__ == "__main__":
    model = PositionalBasedModel(True).parse_from_file("model.decl")
    # print(model.to_asp())
    # pprint(model.to_dict())