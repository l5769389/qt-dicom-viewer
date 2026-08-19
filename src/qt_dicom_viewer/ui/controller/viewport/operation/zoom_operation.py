import math


class ScrollOperation:
    def __init__(
        self,
        threshold: float = 80.0,
    ) -> None:
        self._threshold = threshold
        self._accumulator = 0.0


    def reset(self) -> None:
        self._accumulator = 0.0