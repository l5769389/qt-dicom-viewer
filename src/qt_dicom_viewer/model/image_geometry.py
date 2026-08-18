from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

@dataclass(frozen=True, slots=True)
class Offset:
    x: float
    y: float

@dataclass(frozen=True, slots=True)
class DragUpdateEvent:
    start_position: Point
    current_position: Point
    step_offset: Offset
    total_offset: Offset