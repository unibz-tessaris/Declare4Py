import typing


class Encoder:
    instance = None

    def __new__(cls):
        """
        A singleton class which encodes and decodes the given values. It contains the information of encoded values
        during its lifecycle, so, it can decode the values back.
        """
        if cls.instance is None:
            cls.instance = super(Encoder, cls).__new__(cls)
        return cls.instance

    ENCODE: typing.Dict[str, typing.Dict[str, str]] = {
        "ACTIVITIES": {},
        "ATTRIBUTES": {},
        "ATTR_VALUES": {}
    }
    DECODE: typing.Dict[str, typing.Dict[str, str]] = {
        "ACTIVITIES": {},
        "ATTRIBUTES": {},
        "ATTR_VALUES": {}
    }

    @classmethod
    def encode_value(cls, value_type: str, value: any):

        if value not in cls.ENCODE[value_type].keys():
            encoded = "_" + str(value).lower().strip().replace(" ", "_").replace(":", "_") + "_"
            cls.ENCODE[value_type][value] = encoded
            cls.DECODE[value_type][encoded] = value

        return cls.ENCODE[value_type][value]

    @classmethod
    def encode_values(cls, value_type: str, values: typing.List[any]):
        encoded_values: typing.List[str] = []
        for value in values:
            encoded_values.append(cls.encode_value(value_type, value))

        return encoded_values

    @classmethod
    def decode_value(cls, value_type: str, value: str):
        return cls.DECODE[value_type][value] if value in cls.DECODE[value_type].keys() else None
