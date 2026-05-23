from __future__ import annotations

from dataclasses import dataclass, field

from fantasy_strategy_sandbox.world.models import TileCoord


@dataclass(frozen=True)
class AttackDefinition:
    name: str
    attack_bonus: int
    damage: str
    range: int


@dataclass(frozen=True)
class ActionDefinition:
    id: str
    name: str
    resource_cost: str
    target_type: str
    attack_name: str | None = None
    attack_index: int | None = None
    range: int | None = None


@dataclass(frozen=True)
class DamageRoll:
    expression: str
    rolled_dice_count: int
    dice_sides: int
    dice_values: tuple[int, ...]
    modifier: int
    total: int
    critical: bool = False


@dataclass(frozen=True)
class ActionResolution:
    action_id: str
    actor_id: str
    target_id: str
    attack_name: str
    raw_roll: int
    attack_bonus: int
    total_roll: int
    target_ac: int
    outcome: str
    hit: bool
    critical: bool
    target_hp_before: int
    target_hp_after: int
    damage: DamageRoll | None = None


@dataclass(frozen=True)
class UnitDefinition:
    id: str
    name: str
    team: str
    spawn_id: str
    max_hp: int
    hp: int
    ac: int
    speed: int
    initiative_bonus: int
    attacks: list[AttackDefinition]


@dataclass(frozen=True)
class EncounterDefinition:
    encounter_id: str
    map_id: str
    initiative_seed: int
    units: list[UnitDefinition]


@dataclass
class UnitState:
    id: str
    name: str
    team: str
    tile_position: TileCoord
    max_hp: int
    hp: int
    ac: int
    speed: int
    initiative_bonus: int
    attacks: list[AttackDefinition]
    alive: bool = True


@dataclass
class TurnState:
    round_number: int
    initiative_order: list[str]
    initiative_seed: int
    active_unit_id: str
    turn_phase: str
    remaining_movement: int
    action_available: bool
    bonus_action_available: bool
    reaction_available: bool
    turn_index: int = 0


@dataclass
class EncounterState:
    encounter_id: str
    map_id: str
    units: dict[str, UnitState]
    turn: TurnState
    status: str = "active"
    winner_team: str | None = None
    log: list[str] = field(default_factory=list)
    last_resolution: ActionResolution | None = None
