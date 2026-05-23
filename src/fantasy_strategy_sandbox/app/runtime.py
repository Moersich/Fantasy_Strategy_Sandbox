from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fantasy_strategy_sandbox.combat.models import ActionDefinition, EncounterDefinition, EncounterState
from fantasy_strategy_sandbox.combat.turn_engine import TurnEngine
from fantasy_strategy_sandbox.content.loaders import load_encounter, load_map
from fantasy_strategy_sandbox.world.models import GameMap


@dataclass(frozen=True)
class Command:
    type: str
    unit_id: str | None = None
    target: dict[str, int] | None = None
    target_id: str | None = None
    action_id: str | None = None
    attack_index: int | None = None


class GameRuntime:
    def __init__(
        self,
        game_map: GameMap,
        encounter_definition: EncounterDefinition,
        turn_engine: TurnEngine | None = None,
    ) -> None:
        """Build a runtime around one map and one encounter definition.

        Args:
            game_map: Loaded map data. Width and height must be positive and all
                referenced tiles/spawns must already be validated.
            encounter_definition: Encounter content bound to ``game_map``. The
                encounter must reference the same ``map_id`` and contain at
                least one unit.
            turn_engine: Optional combat engine instance. When provided it must
                accept the same command contracts as ``TurnEngine``.
        """
        self.game_map = game_map
        self.encounter_definition = encounter_definition
        self.turn_engine = turn_engine or TurnEngine()
        self.encounter_state: EncounterState | None = None

    @classmethod
    def from_files(cls, map_path: str | Path, encounter_path: str | Path) -> "GameRuntime":
        """Load map and encounter content from disk and return a ready runtime.

        Args:
            map_path: Absolute or relative path to a map JSON file. Relative
                paths may point into the repository root.
            encounter_path: Absolute or relative path to an encounter JSON
                file. Relative paths may point into the repository root.
        """
        game_map = load_map(_resolve_content_path(map_path))
        encounter_definition = load_encounter(_resolve_content_path(encounter_path))
        return cls(game_map=game_map, encounter_definition=encounter_definition)

    def start_encounter(self) -> EncounterState:
        """Instantiate mutable combat state for the configured encounter."""
        self.encounter_state = self.turn_engine.start_encounter(
            game_map=self.game_map,
            encounter_definition=self.encounter_definition,
        )
        return self.encounter_state

    def execute(self, command: Command) -> EncounterState:
        """Apply one combat command to the active encounter state.

        Args:
            command: Command payload for the combat core. ``type`` must be a
                supported command name. Optional fields such as ``target``,
                ``target_id``, ``action_id``, and ``attack_index`` must match
                the selected command semantics. Coordinate payloads use integer
                tile values inside the loaded map bounds. ``attack_index`` must
                be ``>= 0`` when provided.
        """
        state = self.current_state()
        self.encounter_state = self.turn_engine.execute(
            state=state,
            game_map=self.game_map,
            command=command,
        )
        return self.encounter_state

    def current_state(self) -> EncounterState:
        """Return the current mutable encounter state after startup."""
        if self.encounter_state is None:
            raise RuntimeError("Encounter has not been started.")
        return self.encounter_state

    def available_actions(self, unit_id: str | None = None) -> list[ActionDefinition]:
        """List actions currently available to the active unit.

        Args:
            unit_id: Optional unit identifier. ``None`` means the current active
                unit. When provided it must match the active unit id exactly.
        """
        state = self.current_state()
        return self.turn_engine.available_actions(state=state, unit_id=unit_id)

    def legal_targets_for_action(
        self,
        action_id: str,
        unit_id: str | None = None,
        attack_index: int | None = None,
    ) -> list[str]:
        """Return legal target unit ids for a specific action choice.

        Args:
            action_id: Action identifier supported by the combat core. The
                current implementation accepts ``"attack"``.
            unit_id: Optional acting unit id. ``None`` means the active unit.
                Any explicit value must identify that same active unit.
            attack_index: Optional attack selection on the acting unit. ``None``
                selects the default attack at index ``0``. Explicit values must
                be integers in ``[0, len(unit.attacks) - 1]``.
        """
        state = self.current_state()
        return self.turn_engine.legal_targets_for_action(
            state=state,
            action_id=action_id,
            unit_id=unit_id,
            attack_index=attack_index,
        )

    def summary(self) -> dict[str, Any]:
        """Build a UI-friendly snapshot of the encounter state."""
        state = self.current_state()
        return {
            "encounter_id": state.encounter_id,
            "map_id": state.map_id,
            "round_number": state.turn.round_number,
            "active_unit_id": state.turn.active_unit_id,
            "status": state.status,
            "last_resolution": (
                {
                    "action_id": state.last_resolution.action_id,
                    "actor_id": state.last_resolution.actor_id,
                    "target_id": state.last_resolution.target_id,
                    "attack_name": state.last_resolution.attack_name,
                    "raw_roll": state.last_resolution.raw_roll,
                    "attack_bonus": state.last_resolution.attack_bonus,
                    "total_roll": state.last_resolution.total_roll,
                    "target_ac": state.last_resolution.target_ac,
                    "outcome": state.last_resolution.outcome,
                    "hit": state.last_resolution.hit,
                    "critical": state.last_resolution.critical,
                    "target_hp_before": state.last_resolution.target_hp_before,
                    "target_hp_after": state.last_resolution.target_hp_after,
                    "damage": (
                        {
                            "expression": state.last_resolution.damage.expression,
                            "rolled_dice_count": state.last_resolution.damage.rolled_dice_count,
                            "dice_sides": state.last_resolution.damage.dice_sides,
                            "dice_values": list(state.last_resolution.damage.dice_values),
                            "modifier": state.last_resolution.damage.modifier,
                            "total": state.last_resolution.damage.total,
                            "critical": state.last_resolution.damage.critical,
                        }
                        if state.last_resolution.damage is not None
                        else None
                    ),
                }
                if state.last_resolution is not None
                else None
            ),
            "available_actions": [
                {
                    "id": action.id,
                    "name": action.name,
                    "resource_cost": action.resource_cost,
                    "target_type": action.target_type,
                    "attack_name": action.attack_name,
                    "attack_index": action.attack_index,
                    "range": action.range,
                }
                for action in self.available_actions()
            ],
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


def _resolve_content_path(path: str | Path) -> Path:
    """Resolve absolute and project-relative content paths.

    Args:
        path: Candidate filesystem path. Absolute paths are returned unchanged.
            Relative paths may already exist in the current working directory or
            under the repository root.
    """
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate

    project_root = Path(__file__).resolve().parents[3]
    resolved = project_root / candidate
    if resolved.exists():
        return resolved
    return candidate
