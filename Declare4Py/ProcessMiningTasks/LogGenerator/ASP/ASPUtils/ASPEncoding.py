import typing


class ASPEncoder:
    """
    A class which create the encoding for the ASP.
    """

    __value: str = "time(1..t). %t = lunghezza traccia\n" \
                   "cur_state(I,S,0) :- initial(Name,S),template(I,Name).\n"

    __val2 = "{assigned_value(K,V,T) : value(K,V)} = 1 :- trace(A,T), has_attribute(A,K).\n" \
             "cur_state(I,S2,T) :- cur_state(I,S1,T-1), template(I,Name), automaton(Name,S1,c,S2), trace(A,T), not activation(I,A), not target(I,A).\n" \
             "cur_state(I,S2,T) :- cur_state(I,S1,T-1), template(I,Name), automaton(Name,S1,c,S2), trace(A,T), activation(I,A), not activation_condition(I,T).\n" \
             "cur_state(I,S2,T) :- cur_state(I,S1,T-1), template(I,Name), automaton(Name,S1,a,S2), trace(A,T), activation(I,A), activation_condition(I,T).\n" \
             "cur_state(I,S2,T) :- cur_state(I,S1,T-1), template(I,Name), automaton(Name,S1,c,S2), trace(A,T), target(I,A), not correlation_condition(I,T).\n" \
             "cur_state(I,S2,T) :- cur_state(I,S1,T-1), template(I,Name), automaton(Name,S1,b,S2), trace(A,T), target(I,A), correlation_condition(I,T).\n" \
             "sat(I,T) :- cur_state(I,S,T), template(I,Name), accepting(Name,S).\n"

    __val4 = """#show trace/2.\n#show assigned_value/3.\n%#show sat/2.\n"""

    @classmethod
    def get_asp_encoding(cls, facts_name: typing.Union[typing.List[str], None] = None, is_sat: bool = True):
        """
        We need add the facts. The facts name can be anything described in the decl model.
        Parameters
        ----------
        facts_name

        is_sat

        Returns
        -------

        """

        if facts_name is None:
            facts_name = ["activity"]
        if not isinstance(facts_name, list):
            raise ValueError(f"facts_name is not of type list!")

        val3: str = ":- sat(I), not sat(I,t).\n"
        if not is_sat:
            val3 += ":- unsat(I), sat(I,t).\n"

        ls = []
        fact_contains = []
        for n in facts_name:
            if n.lower() not in fact_contains:
                ls.append(f"{{trace(A,T) : {n}(A)}} = 1 :- time(T).")
                fact_contains.append(n.lower())
        return cls.__value + "\n".join(ls) + "\n" + cls.__val2 + "\n" + val3 + "\n" + cls.__val4

if __name__ == "__main__":
    print(ASPEncoder.get_asp_encoding(is_sat=False))