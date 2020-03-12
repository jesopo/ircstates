from typing import Any, Dict, List

def line_handler_decorator(d: Dict[str, List[Any]]):
    def line_handler(command: str):
        def _(func: Any):
            if not command in d:
                d[command] = []
            d[command].append(func)
        return _
    return line_handler
