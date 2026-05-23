from __future__ import annotations

from pathlib import Path

from fantasy_strategy_sandbox.app.runtime import GameRuntime

_TRAINING_MAP_PATH = Path("data/maps/training-yard.json")
_TRAINING_ENCOUNTER_PATH = Path("data/encounters/training-yard-skirmish.json")


def create_training_yard_runtime(start_encounter: bool = True) -> GameRuntime:
    # Keep both runtime modes bound to the same content fixture so the viewer
    # remains an adapter over the core instead of a second gameplay path.
    runtime = GameRuntime.from_files(_TRAINING_MAP_PATH, _TRAINING_ENCOUNTER_PATH)
    if start_encounter:
        runtime.start_encounter()
    return runtime
