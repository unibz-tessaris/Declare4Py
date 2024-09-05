from Declare4Py.ProcessModels.DeclareModel import *

"""
Test suite for the class Declare4PyModel.DeclareToken 
"""


def declare_token_test(
        model_name: typing.Union[str, any],
        model_type: typing.Union[str, any],
        expected_encoded_name: typing.Union[str, any]
):
    """
    Asserts if the dictionary of the DeclareModelToken corresponds to the expected dictionary.
    This tests the method to_dict() of the class that also uses the methods get_name() and get_encoded_name()
    Since the Encoder class implements the singleton pattern the expected_encoded_name should increment while inserting
    new values

    Parameters
    model_name: str | any
        The name of the model
    model_type: str | any
        The type of the model
    expected_encoded_name: str | any
        The expected encoded value
    ----------

    """
    expected_model_type = "other"
    if model_type in ["event_name", "event_value", "attr_name", "attr_val"]:
        expected_model_type = model_type

    expected_dict: typing.Dict[str, str] = {
        expected_model_type: str(model_name),
        f"encoded_{str(expected_model_type)}": str(expected_encoded_name)
    }

    model: DeclareModelToken = DeclareModelToken(model_name, model_type)
    assert model.to_dict() == expected_dict


def declare_token_suite_tests():
    """
    Tests the functionality of the DeclareModelToken class and the Decoder class
    Creates 2 instances of each model type in order to ensure that the encoding procedure is working for each type
    """

    print("Declaration of the DeclareModelToken with different types: Initialization")

    declare_token_test("event1", "event_name", "event_name_0")
    declare_token_test("event2", "event_name", "event_name_1")

    declare_token_test("value1", "event_value", "event_value_0")
    declare_token_test("value2", "event_value", "event_value_1")

    declare_token_test("attr1", "attr_name", "attr_name_0")
    declare_token_test("attr2", "attr_name", "attr_name_1")

    declare_token_test("value1", "attr_val", "attr_val_0")
    declare_token_test("value2", "attr_val", "attr_val_1")

    declare_token_test("other1", "type", "other_0")
    declare_token_test("other2", "type", "other_1")

    print("Declaration of the DeclareModelToken with different types: Success")

    """
    Furthermore the creation of an already created token should return the same expected encoded name
    """

    print("Existing DeclareModelToken should return an existent value: Initialization")

    declare_token_test("attr1", "attr_name", "attr_name_0")

    print("Existing DeclareModelToken should return an existent value: Success")

    """
    Invalid inputs should raise a Value Error Exception
    """

    print("Invalid DeclareModelToken should return an error: Initialization")

    try:
        declare_token_test(4444, "invalid", "invalid")
        assert False
    except ValueError:
        assert True

    print("Invalid DeclareModelToken should return an error: Success")


if __name__ == "__main__":
    """
    Starts with the token declaration test
    """
    declare_token_suite_tests()
