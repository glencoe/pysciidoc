from inspect import Signature


class SignatureFormatter:
    """Format a routine signature to make it fit into a maximum width."""

    def __init__(self) -> None:
        self.max_width = 50

    def format(self, s: Signature) -> str:
        result = ["("]
        for param in s.parameters.values():
            annotation = param.annotation
            if annotation == param.empty:
                annotation = ""
            elif isinstance(annotation, type):
                annotation = f": {annotation.__name__.split('.')[-1]}"
            else:
                annotation = f": {str(annotation).split('.')[-1]}"

            default = param.default
            if default == param.empty:
                default = ""
            elif annotation != "":
                default = f" = {default}"
            else:
                default = f"={default}"

            result.append(f"{param.name}{annotation}{default}")

        if s.return_annotation != s.empty:
            if isinstance(s.return_annotation, type):
                result.append(f") -> {s.return_annotation.__name__.split('.')[-1]}")
            else:
                result.append(f") -> {str(s.return_annotation).split('.')[-1]}")
        else:
            result.append(")")
        oneline = "".join(result[0:2])
        if len(result) > 2:
            oneline = ", ".join([oneline] + result[2:-1])
            oneline = f"{oneline}{result[-1]}"
        if len(oneline) <= self.max_width:
            return oneline
        else:
            start = "\n  ".join(result[0:2])
            middle = ",\n  ".join([start] + result[2:-1])
            end = result[-1]
            return "".join([middle, end])
