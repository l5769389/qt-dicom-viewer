import math


class ScrollOperation:
    def __init__(
        self,
        threshold: float = 80.0,
    ) -> None:
        self._threshold = threshold
        self._accumulator = 0.0

    def handle_wheel(
        self,
        *,
        angle_delta_y: float,
        current_index: int,
        slice_count: int,
    ) -> int | None:
        if angle_delta_y == 0:
            return None

        if slice_count <= 0:
            return None

        # 滚动方向改变时清理之前的残余量。
        if (
            self._accumulator != 0
            and self._accumulator
                * angle_delta_y < 0
        ):
            self._accumulator = 0.0

        self._accumulator += angle_delta_y

        steps = math.trunc(
            self._accumulator / self._threshold
        )

        if steps == 0:
            return None

        self._accumulator -= (
            steps * self._threshold
        )

        next_index = current_index - steps

        next_index = max(
            0,
            min(next_index, slice_count - 1),
        )

        if next_index == current_index:
            return None

        return next_index

    def reset(self) -> None:
        self._accumulator = 0.0