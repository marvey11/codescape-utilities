class DatumInContext:
    value: object

class JSONPath:
    def find(self, data: object) -> list[DatumInContext]: ...

def parse(string: str) -> JSONPath: ...
