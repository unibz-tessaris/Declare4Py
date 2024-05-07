from abc import abstractmethod


class DeclareFunctions:

    DECL_ACTIVITY = "activity"
    DECL_BIND = "bind"
    DECL_INTEGER_BETWEEN = "integer between"
    DECL_FLOAT_BETWEEN = "float between"

    DECL_POSITION = {"function": "pos", "negated": "!pos", "attr_count": 2}
    DECL_PAYLOAD = {"function": "payload", "negated": "!payload", "attr_count": 3}

    DECL_FILE_EXTENSION = ".decl"

    @classmethod
    def line_starts_with_constraint(cls, line) -> bool:
        return (line.lower().startswith(cls.DECL_POSITION["function"]) or
                line.lower().startswith(cls.DECL_POSITION["negated"]) or
                line.lower().startswith(cls.DECL_PAYLOAD["function"]) or
                line.lower().startswith(cls.DECL_PAYLOAD["negated"]))

class DeclareEntity:

    @abstractmethod
    def to_declare(self) -> str:
        pass
