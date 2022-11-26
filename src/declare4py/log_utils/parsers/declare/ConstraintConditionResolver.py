import re
from enum import Enum


class DECLARE_LOGIC_OP(str, Enum):

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = str.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, operator_name: str, token: str, symbol: str):
        self.operator = operator_name
        self.token = token
        self.symbol = symbol

    AND = "and", "AND", "and"  # TODO: don't yet whether declare model can have && sybmol as and
    OR = "or", "OR", "or"  # TODO: don't yet whether declare model can have || sybmol as or
    GT = "greater_then", "GT", ">"
    GEQ = "greater_eq", "GEQ", ">="
    LT = "less_then", "LT", "<"
    LEQ = "less_eq", "LEQ", "<="
    EQ = "equal", "EQ", "="  # TODO: would be converted in "is"
    NEQ = "not_equal", "NEQ", "!="  # TODO: should convert into  is not

    IS = "is", "IS", "is"
    IS_NOT = "is not", "IS_NOT", "is not"
    IN = "in", "IN", "in"
    IN_NOT = "not in", "NOT_IN", "not in"

    SAME = "same", "SAME", "same"  # TODO: not implemented yet
    different = "different", "DIFFERENT", "different"  # TODO: not implemented yet
    exist = "exist", "EXIST", "exist"  # TODO: not implemented yet

    @classmethod
    def get_logic_op_from_string(cls, name):
        return next(filter(lambda t: t.operator == name, DECLARE_LOGIC_OP), None)

    @classmethod
    def get_token(cls, token: str):
        token = re.sub(" +", " ", token)
        token = re.sub(" ", "_", token)
        return tuple(filter(lambda t: t.token.lower() == token.lower(), DECLARE_LOGIC_OP))

    def __str__(self):
        return "<LOGIC_OP:" + str(self.operator) + ": " + str(self.value) + " >"

    def __repr__(self):
        return "\""+str(self.__str__())+"\""


class DeclareConditionTokenizer:

    # operatorsRegex = r" *(is_not|is|not_in|in|or|and|not|same|different|exist|<=|>=|<|>|=|!=) *"
    operatorsRegex = r" *(is_not|is|not_in|in|or|and|not|<=|>=|<|>|=|!=) *"

    def __normalize_condition(self, condition: str) -> str:
        string = re.sub(r'\)', ' ) ', condition)
        string = re.sub(r'\(', ' ( ', string)
        string = string.strip()
        string = re.sub(' +', ' ', string)
        string = re.sub(r'is not', 'is_not', string)
        string = re.sub(r'not in', 'not_in', string)
        string = re.sub(r' *> *', '>', string)
        string = re.sub(r' *< *', '<', string)
        string = re.sub(r' *= *', '=', string)
        string = re.sub(r' *!= *', '!=', string)
        string = re.sub(r' *is *', '=', string)
        string = re.sub(r' *is *not *', '!=', string)
        string = re.sub(r' *<= *', '<=', string)
        string = re.sub(r' *>= *', '>=', string)
        return string

    def tokenize(self, condition: str):
        normalized_condition = self.__normalize_condition(condition)
        if len(normalized_condition) == 0:
            return normalized_condition
        split_cond = normalized_condition.split(" ")
        total_len = len(split_cond)
        new_cond, last_str, idx, st = [], "", 0, ""
        # for idx, st in enumerate(split_cond):
        while total_len > idx:
            st = split_cond[idx]
            matches = re.match(r" *(not_in|in) *", st)
            if matches:
                new_cond = new_cond[:-1]  # remove last element added which should be last_Str, which must be an attr
                next_word = split_cond[idx + 1].strip()  # must be "(" after in or not_in
                # my_str = f"{last_str} {DECLARE_LOGIC_OP.get_token()} "
                my_str = f"{last_str} {st} "
                if next_word != '(':
                    raise SyntaxError(f"Unable to parse the condition. After in keyword expected \"(\""
                                      f" but found {next_word}")
                while next_word != ")":
                    idx = idx + 1
                    my_str = f"{my_str} {next_word}"
                    next_word = split_cond[idx]
                    if next_word == "(":
                        pass  # something wrong in the condition something like this "A.grade in (dx,(dfd, ere)"
                        #                                                              ..............^ unhandled
                new_cond.append(my_str)
            # elif st.startswith("(") or st == '(':

            else:
                new_cond.append(st)
            last_str = st
            idx = idx + 1
        print(normalized_condition)
        print(split_cond)

    def __tokenize_in_not_in(self, split_cond: [str], idx: int) -> (str, int):
        next_word = split_cond[idx + 1].strip()  # must be "(" after in or not_in
        # my_str = f"{last_str} {DECLARE_LOGIC_OP.get_token()} "
        # my_str = f"{last_str} {st} "
        # if next_word != '(':
        #     raise SyntaxError(f"Unable to parse the condition. After in keyword expected \"(\""
        #                       f" but found {next_word}")
        # while next_word != ")":
        #     idx = idx + 1
        #     my_str = f"{my_str} {next_word}"
        #     next_word = split_cond[idx]
        #     if next_word == "(":
        #         pass  # something wrong in the condition something like this "A.grade in (dx,(dfd, ere)"
        #         #
        pass