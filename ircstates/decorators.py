from typing import Any, Dict, List

def handler_decorator(d: Dict[str, List[Any]]):
    def _handler(command: str):
        def _(func: Any):
            if not command in d:
                d[command] = []
            d[command].append(func)
            return func
        return _
    return _handler
