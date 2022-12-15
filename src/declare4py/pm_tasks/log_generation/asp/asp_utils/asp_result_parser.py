import json

import clingo
import typing
from clingo import SymbolType


class ASPResultEventModel:

    def __init__(self, fact_symbol: [clingo.symbol.Symbol]):
        self.name: str
        self.pos: int
        self.resource: {str, str} = {}
        self.fact_symbol: [clingo.symbol.Symbol] = fact_symbol
        self.parse_clingo_event()

    def parse_clingo_event(self):
        for symbols in self.fact_symbol:
            # syb: clingo.symbol.Symbol = symbols
            if symbols.type == SymbolType.Function:
                # print(syb.positive)
                self.name = str(symbols.name)
            if symbols.type == SymbolType.Number:
                self.pos = symbols.number

    def __str__(self) -> str:
        st = f"""{{ "event_name":"{self.name}", "position": "{self.pos}", "resource_or_value": {self.resource} }}"""
        return st.replace("'", '"')

    def __repr__(self) -> str:
        return self.__str__()


class ASPResultTraceModel:
    def __init__(self, trace_name: str, model: [clingo.solving.Model], scale_down: int):
        self.model = model
        self.name: str = trace_name
        self.events: [ASPResultEventModel] = []
        # ASP/clingo doesn't handle floats, thus we scaling up the number values and now, we have to scale down back
        # after result
        self.scale_down_number = scale_down
        self.parse_clingo_trace()

    def parse_clingo_trace(self):
        e = {}
        assigned_values_symbols = []
        for m in self.model:  # self.model = [trace(),.. trace(),.., assigned_value(...),...]
            trace_name = str(m.name)
            if trace_name == "trace":  # fact "trace(event_name, position)"
                eventModel = ASPResultEventModel(m.arguments)
                e[eventModel.pos] = eventModel
                self.events.append(eventModel)
            if trace_name == "assigned_value":
                assigned_values_symbols.append(m.arguments)

        for assigned_value_symbol in assigned_values_symbols:
            resource_name, resource_val, pos = self.parse_clingo_val_assignement(assigned_value_symbol)
            event = e[pos]
            event.resource[resource_name] = resource_val

    def parse_clingo_val_assignement(self, syb: [clingo.symbol.Symbol]):
        val = []
        tot_symbols = len(syb)
        for i, symbols in enumerate(syb):
            if symbols.type == SymbolType.Function:  # if symbol is functionm it can have .arguments
                val.append(symbols.name)
            else:
                num = symbols.number
                # we shouldn't scale the last number of given symbol because it referred to the trace
                # position and not attribute values
                # if (tot_symbols - 1) != i:
                #     num = (symbols.number / self.scale_down_number)
                val.append(num)
        return val[0], val[1], val[2]

    def __str__(self):
        st = f"""{{ "trace_name": "{self.name}", "events": {self.events} }}"""
        return st.replace("'", '"')

    def __repr__(self):
        return self.__str__()


class AspResultLogModel:
    def __init__(self):
        self.traces: typing.List[ASPResultTraceModel] = []

    def __str__(self):
        return str(self.traces)

    def __repr__(self):
        return self.__str__()

    def print_indent(self):
        s = self.__str__()
        j = json.loads(s)
        print(json.dumps(j, indent=2))
