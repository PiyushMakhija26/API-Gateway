from typing import List, Any
import itertools

class RoundRobinLoadBalancer:
    def __init__(self, targets: List[Any]):
        self.targets = targets
        self._iterator = itertools.cycle(targets) if targets else None

    def get_next(self) -> Any:
        if not self._iterator:
            raise ValueError("No targets available for load balancing")
        return next(self._iterator)
