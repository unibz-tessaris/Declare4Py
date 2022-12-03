try:
    from future import annotations
except:
    pass

class LTLModel:
    def __init__(self, formula: str = None):
        self.formula: str = formula
