import typing


class Encoder:
    instance = None

    # Constructor
    def __new__(cls):
        """
        A singleton class which encodes and decodes the given values. It contains the information of encoded values
        during its lifecycle, so, it can decode the values back.
        """
        if cls.instance is None:
            cls.instance = super(Encoder, cls).__new__(cls)
        return cls.instance

    # Encoder dictionary for encoding and decoding
    Encoder: typing.Dict[str, typing.Dict[str, str]] = {
        "ENCODE": {},
        "DECODE": {}
    }

    # Encoding element name
    ENCODING_ELEMENT_NAME = "_encoded_element_{}_"

    # Encoded elements count
    __COUNT = 1

    @classmethod
    def create_and_encode_value(cls, value: any) -> str:
        """
        Creates an encoded entry for the value if not in the encoder dictionary
        Returns the encoed value
        """
        if value not in list(cls.Encoder["ENCODE"].keys()):
            encoded = cls.ENCODING_ELEMENT_NAME.format(str(cls.__COUNT))
            cls.Encoder["ENCODE"][value] = encoded
            cls.Encoder["DECODE"][encoded] = value
            cls.__COUNT += 1

        return cls.Encoder["ENCODE"][value]

    @classmethod
    def encode_value(cls, value: any) -> str:
        """
        Tries to encode a value, if the value is not encoded it will raise a ValueError
        """
        if value not in list(cls.Encoder["ENCODE"].keys()):
            raise ValueError(f"Value {value} is not encoded and probably not declared in the model. Check your definitions")
        return cls.Encoder["ENCODE"][value]

    @classmethod
    def create_and_encode_values(cls, values: typing.List[any]) -> typing.List[str]:
        """
        Encodes a list of values and returns a list of encoded values.
        """
        encoded_values: typing.List[str] = []
        for value in values:
            encoded_values.append(cls.create_and_encode_value(value))

        return encoded_values

    @classmethod
    def decode_value(cls, value: str) -> str:
        """
        Decodes a values if it is present in the dictionary, otherwise the value is returned
        """
        return cls.Encoder["DECODE"][value] if value in cls.Encoder["DECODE"].keys() else value

    @classmethod
    def reset(cls):
        """
        Resets the current Instance of the Encoder
        """
        cls.instance = None
