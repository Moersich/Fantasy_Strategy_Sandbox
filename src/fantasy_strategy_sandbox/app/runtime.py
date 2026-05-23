from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fantasy_strategy_sandbox.combat.models import EncounterDefinition, EncounterState
from fantasy_strategy_sandbox.combat.turn_engine import TurnEngine
from fantasy_strategy_sandbox.content.loaders import load_encounter, load_map
from fantasy_strategy_sandbox.world.models import GameMap


@dataclass(frozen=True)
class Command:
    type: str
    unit_id: str | None = None
    target: dict[str, int] | None = None
    target_id: str | None = None


class GameRuntime:
    def __init__(
        self,
        game_map: GameMap,
        encounter_definition: EncounterDefinition,
        turn_engine: TurnEngine | None = None,
    ) -> None:
        self.game_map = game_map
        self.encounter_definition = encounter_definition
        self.turn_engine = turn_engine or TurnEngine()
        self.encounter_state: EncounterState | None = None

    @classmethod
    def from_files(cls, map_path: str | Path, encounter_path: str | Path) -> "GameRuntime":
        game_map = load_map(Path(map_path))
        encounter_definition = load_encounter(Path(encounter_path))
        return cls(game_map=game_map, encounter_definition=encounter_definition)

    def start_encounter(self) -> EncounterState:
        self.encounter_state = self.turn_engine.start_encounter(
            game_map=self.game_map,
            encounter_definition=self.encounter_definition,
        )
        return self.encounter_state

    def execute(self, command: Command) -> EncounterState:
        if self.encounter_state is None:
            raise RuntimeError("Encounter has not been started.")
        self.encounter_state = self.turn_engine.execute(
            state=self.encounter_state,
            game_map=self.game_map,
            command=command,
        )
        return self.encounter_state

    def summary(self) -> dict[str, Any]:
        if self.encounter_state is None:
            raise RuntimeError("Encounter has not been started.")
        state = self.encounter_state
        return {
            "encounter_id": state.encounter_id,
            "map_id": state.map_id,
            "round_number": state.turn.round_number,
            "active_unit_id": state.turn.active_unit_id,
            "status": state.status,
            "units": [
                {
                    "id": unit.id,
                    "team": unit.team,
                    "position": {"x": unit.tile_position.x, "y": unit.tile_position.y},
                    "hp": unit.hp,
                    "max_hp": unit.max_hp,
                    "alive": unit.alive,
                }
                for unit in state.units.values()
            ],
        }
