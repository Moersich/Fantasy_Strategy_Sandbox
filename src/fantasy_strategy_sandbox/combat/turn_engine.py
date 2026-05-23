from __future__ import annotations

import random
import re
from typing import Iterable

from fantasy_strategy_sandbox.combat.models import (
    ActionDefinition,
    ActionResolution,
    DamageRoll,
    EncounterDefinition,
    EncounterState,
    TurnState,
    UnitDefinition,
    UnitState,
)
from fantasy_strategy_sandbox.queries.movement import grid_distance, reachable_tiles
from fantasy_strategy_sandbox.world.models import GameMap, TileCoord

_DICE_RE = re.compile(r"^(?P<count>\d+)d(?P<sides>\d+)(?P<modifier>[+-]\d+)?$")


class TurnEngine:
    def start_encounter(self, game_map: GameMap, encounter_definition: EncounterDefinition) -> EncounterState:
        """Create the initial mutable encounter state for one combat.

        Args:
            game_map: Loaded map for the encounter. The map must already be
                validated and share the same ``map_id`` as the encounter.
            encounter_definition: Static encounter content. It must contain at
                least one unit and a non-negative initiative seed.
        """
        if encounter_definition.map_id != game_map.map_id:
            raise ValueError(
                f"Encounter map id {encounter_definition.map_id} does not match loaded map {game_map.map_id}."
            )

        units = self._instantiate_units(game_map, encounter_definition.units)
        order = self._roll_initiative(encounter_definition.units, encounter_definition.initiative_seed)
        if not order:
            raise ValueError("Encounter must contain at least one unit.")

        first_unit = units[order[0]]
        turn = TurnState(
            round_number=1,
            initiative_order=order,
            initiative_seed=encounter_definition.initiative_seed,
            active_unit_id=first_unit.id,
            turn_phase="await_command",
            remaining_movement=first_unit.speed,
            action_available=True,
            bonus_action_available=True,
            reaction_available=True,
            turn_index=0,
        )
        return EncounterState(
            encounter_id=encounter_definition.encounter_id,
            map_id=encounter_definition.map_id,
            units=units,
            turn=turn,
            log=[f"Encounter started. Active unit: {first_unit.id}."],
        )

    def execute(self, state: EncounterState, game_map: GameMap, command: object) -> EncounterState:
        """Validate and resolve one command against the current encounter.

        Args:
            state: Mutable encounter state in ``"active"`` status.
            game_map: Authoritative map used for spatial validation. Tile
                coordinates must stay inside this map.
            command: Any object with a ``type`` attribute and the fields needed
                by that command. Supported command types are ``move_unit``,
                ``use_action``, ``attack_target``, ``dash``, and ``end_turn``.
        """
        if state.status != "active":
            raise ValueError("Encounter is not active.")

        command_type = getattr(command, "type", None)
        if not command_type:
            raise ValueError("Command requires a type.")

        if command_type == "move_unit":
            self._move_unit(state, game_map, command)
        elif command_type == "use_action":
            self._use_action(state, command)
        elif command_type == "attack_target":
            self._use_action(state, command, fallback_action_id="attack")
        elif command_type == "dash":
            self._dash(state, command)
        elif command_type == "end_turn":
            self._require_active_unit(state, getattr(command, "unit_id"))
            self._end_turn(state)
        else:
            raise ValueError(f"Unsupported command type {command_type}.")

        self._update_winner(state)
        return state

    def available_actions(self, state: EncounterState, unit_id: str | None = None) -> list[ActionDefinition]:
        """Return the action definitions the acting unit may currently use.

        Args:
            state: Mutable encounter state with an active unit.
            unit_id: Optional acting unit id. ``None`` resolves to the active
                unit. Explicit values must equal ``state.turn.active_unit_id``.
        """
        actor = self._require_active_unit(state, unit_id or state.turn.active_unit_id)
        if not actor.alive or not state.turn.action_available:
            return []
        if not actor.attacks:
            return []

        attack = actor.attacks[0]
        return [
            ActionDefinition(
                id="attack",
                name="Attack",
                resource_cost="action",
                target_type="unit",
                attack_name=attack.name,
                attack_index=0,
                range=attack.range,
            )
        ]

    def legal_targets_for_action(
        self,
        state: EncounterState,
        action_id: str,
        unit_id: str | None = None,
        attack_index: int | None = None,
    ) -> list[str]:
        """Return legal target ids for one action choice.

        Args:
            state: Mutable encounter state with an active unit.
            action_id: Supported action id. The current implementation accepts
                only ``"attack"``.
            unit_id: Optional acting unit id. ``None`` resolves to the active
                unit. Explicit values must equal the active unit id.
            attack_index: Optional selected attack profile. ``None`` means index
                ``0``. Explicit values must be integers in the available attack
                index range for the acting unit.
        """
        actor = self._require_active_unit(state, unit_id or state.turn.active_unit_id)
        if action_id != "attack":
            raise ValueError(f"Unsupported action id {action_id}.")
        if not state.turn.action_available:
            return []

        attack = self._select_attack(actor, attack_index)
        legal_targets = [
            unit.id
            for unit in state.units.values()
            if self._is_attack_target_in_range(actor=actor, target=unit, attack=attack)
        ]
        legal_targets.sort()
        return legal_targets

    def _instantiate_units(self, game_map: GameMap, unit_definitions: Iterable[UnitDefinition]) -> dict[str, UnitState]:
        """Create encounter unit state from static unit definitions.

        Args:
            game_map: Loaded map whose spawn ids must contain every referenced
                ``spawn_id`` from ``unit_definitions``.
            unit_definitions: Iterable of static units. Each unit must have
                positive ``max_hp`` and ``ac``, non-negative ``speed``, and a
                unique id.
        """
        units: dict[str, UnitState] = {}
        occupied: set[TileCoord] = set()
        for definition in unit_definitions:
            if definition.spawn_id not in game_map.spawns:
                raise ValueError(f"Unknown spawn id {definition.spawn_id} for unit {definition.id}.")
            tile_position = game_map.spawns[definition.spawn_id]
            if tile_position in occupied:
                raise ValueError(f"Spawn collision detected at {tile_position}.")
            occupied.add(tile_position)
            units[definition.id] = UnitState(
                id=definition.id,
                name=definition.name,
                team=definition.team,
                tile_position=tile_position,
                max_hp=definition.max_hp,
                hp=definition.hp,
                ac=definition.ac,
                speed=definition.speed,
                initiative_bonus=definition.initiative_bonus,
                attacks=list(definition.attacks),
            )
        return units

    def _roll_initiative(self, unit_definitions: Iterable[UnitDefinition], seed: int) -> list[str]:
        """Roll deterministic initiative order for the provided units.

        Args:
            unit_definitions: Iterable of units to include in initiative. Each
                unit contributes one d20 roll plus its initiative bonus.
            seed: Deterministic random seed. Any integer is accepted.
        """
        rng = random.Random(seed)
        initiative_entries = []
        for definition in unit_definitions:
            roll = rng.randint(1, 20) + definition.initiative_bonus
            initiative_entries.append((roll, definition.initiative_bonus, definition.id))
        initiative_entries.sort(key=lambda entry: (-entry[0], -entry[1], entry[2]))
        return [entry[2] for entry in initiative_entries]

    def _move_unit(self, state: EncounterState, game_map: GameMap, command: object) -> None:
        """Resolve a movement command for the active unit.

        Args:
            state: Mutable encounter state. ``remaining_movement`` must be
                ``>= 0``.
            game_map: Map used to validate walkability and tile bounds.
            command: Object with ``unit_id`` and ``target``. ``target`` must be
                a mapping containing integer ``x`` and ``y`` tile coordinates in
                the loaded map and within the current movement budget.
        """
        actor = self._require_active_unit(state, getattr(command, "unit_id"))
        target_payload = getattr(command, "target")
        if target_payload is None:
            raise ValueError("move_unit requires a target tile.")

        try:
            target = TileCoord(x=int(target_payload["x"]), y=int(target_payload["y"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("move_unit target must include integer x and y coordinates.") from exc
        occupied = {unit.tile_position for unit in state.units.values() if unit.alive}
        reachable = reachable_tiles(
            game_map=game_map,
            start=actor.tile_position,
            movement_budget=state.turn.remaining_movement,
            occupied=occupied,
        )
        if target not in reachable:
            raise ValueError(f"Target tile {target} is not reachable for {actor.id}.")

        cost = reachable[target]
        actor.tile_position = target
        state.turn.remaining_movement -= cost
        state.log.append(f"{actor.id} moved to ({target.x}, {target.y}) for {cost} movement.")

    def _use_action(self, state: EncounterState, command: object, fallback_action_id: str | None = None) -> None:
        """Resolve a first-class action command for the active unit.

        Args:
            state: Mutable encounter state whose active unit still has its main
                action available.
            command: Object with ``unit_id`` plus action-specific fields. For
                the current Attack Action PoC this requires ``target_id`` and
                optionally ``attack_index`` in the valid attack index range.
            fallback_action_id: Optional action id used by compatibility
                wrappers such as ``attack_target``. ``None`` means the command
                must provide its own ``action_id``.
        """
        actor = self._require_active_unit(state, getattr(command, "unit_id"))
        if not state.turn.action_available:
            raise ValueError(f"{actor.id} has already spent its action.")

        action_id = getattr(command, "action_id", None) or fallback_action_id
        if not action_id:
            raise ValueError("use_action requires an action_id.")
        if action_id != "attack":
            raise ValueError(f"Unsupported action id {action_id}.")

        target_id = getattr(command, "target_id")
        if not target_id:
            raise ValueError("Attack Action requires a target_id.")
        if target_id not in state.units:
            raise ValueError(f"Unknown target unit {target_id}.")
        if target_id == actor.id:
            raise ValueError(f"{actor.id} cannot target itself.")

        target = state.units[target_id]
        if not target.alive:
            raise ValueError(f"Target {target.id} is already defeated.")

        attack = self._select_attack(actor, getattr(command, "attack_index", None))
        if not self._is_attack_target_in_range(actor=actor, target=target, attack=attack):
            raise ValueError(f"Target {target.id} is out of range for {actor.id}.")

        rng = random.Random(self._command_seed(state))
        raw_attack_roll = rng.randint(1, 20)
        attack_roll = raw_attack_roll + attack.attack_bonus
        target_hp_before = target.hp
        damage_roll: DamageRoll | None = None
        if raw_attack_roll == 1:
            outcome = "miss"
            hit = False
            critical_hit = False
        elif raw_attack_roll == 20 or attack_roll >= target.ac:
            critical_hit = raw_attack_roll == 20
            damage_roll = _roll_damage(attack.damage, rng, critical=critical_hit)
            target.hp = max(0, target.hp - damage_roll.total)
            target.alive = target.hp > 0
            outcome = "critical_hit" if critical_hit else "hit"
            hit = True
        else:
            outcome = "miss"
            hit = False
            critical_hit = False

        resolution = ActionResolution(
            action_id="attack",
            actor_id=actor.id,
            target_id=target.id,
            attack_name=attack.name,
            raw_roll=raw_attack_roll,
            attack_bonus=attack.attack_bonus,
            total_roll=attack_roll,
            target_ac=target.ac,
            outcome=outcome,
            hit=hit,
            critical=critical_hit,
            target_hp_before=target_hp_before,
            target_hp_after=target.hp,
            damage=damage_roll,
        )
        state.last_resolution = resolution
        state.log.append(_format_attack_resolution(resolution))

        state.turn.action_available = False

    def _dash(self, state: EncounterState, command: object) -> None:
        """Resolve the Dash action for the active unit.

        Args:
            state: Mutable encounter state whose active unit still has its main
                action available.
            command: Object with ``unit_id`` matching the active unit.
        """
        actor = self._require_active_unit(state, getattr(command, "unit_id"))
        if not state.turn.action_available:
            raise ValueError(f"{actor.id} has already spent its action.")
        state.turn.remaining_movement += actor.speed
        state.turn.action_available = False
        state.log.append(f"{actor.id} used Dash and now has {state.turn.remaining_movement} movement.")

    def _end_turn(self, state: EncounterState) -> None:
        """Advance initiative to the next living unit."""
        living_order = [unit_id for unit_id in state.turn.initiative_order if state.units[unit_id].alive]
        if not living_order:
            state.status = "ended"
            state.winner_team = None
            return

        current_index = living_order.index(state.turn.active_unit_id)
        next_index = (current_index + 1) % len(living_order)
        wrapped = next_index == 0
        next_unit = state.units[living_order[next_index]]

        state.turn.initiative_order = living_order
        state.turn.turn_index = next_index
        state.turn.active_unit_id = next_unit.id
        state.turn.turn_phase = "await_command"
        state.turn.remaining_movement = next_unit.speed
        state.turn.action_available = True
        state.turn.bonus_action_available = True
        state.turn.reaction_available = True
        if wrapped:
            state.turn.round_number += 1
        state.log.append(f"It is now {next_unit.id}'s turn.")

    def _update_winner(self, state: EncounterState) -> None:
        """End the encounter when only one living team remains."""
        living_teams = {unit.team for unit in state.units.values() if unit.alive}
        if len(living_teams) == 1:
            state.status = "ended"
            state.winner_team = next(iter(living_teams))
            state.log.append(f"Encounter ended. Winner: {state.winner_team}.")

    def _require_active_unit(self, state: EncounterState, unit_id: str | None) -> UnitState:
        """Return the active unit and reject missing or inactive ids.

        Args:
            state: Mutable encounter state with an active unit id.
            unit_id: Candidate acting unit id. It must be a non-empty string
                equal to ``state.turn.active_unit_id``.
        """
        if unit_id is None:
            raise ValueError("Command requires a unit_id.")
        if state.turn.active_unit_id != unit_id:
            raise ValueError(f"{unit_id} is not the active unit.")
        return state.units[unit_id]

    def _command_seed(self, state: EncounterState) -> int:
        """Derive the deterministic seed for the current command resolution."""
        return state.turn.initiative_seed + state.turn.round_number * 100 + state.turn.turn_index

    def _select_attack(self, actor: UnitState, attack_index: int | None) -> "object":
        """Return one attack profile by index from the acting unit.

        Args:
            actor: Acting unit with one or more attack profiles.
            attack_index: Optional selected index. ``None`` resolves to ``0``.
                Explicit values must be integers in
                ``[0, len(actor.attacks) - 1]``.
        """
        resolved_index = attack_index if attack_index is not None else 0
        if resolved_index < 0 or resolved_index >= len(actor.attacks):
            raise ValueError(f"{actor.id} does not have attack index {resolved_index}.")
        return actor.attacks[resolved_index]

    def _is_attack_target_in_range(self, actor: UnitState, target: UnitState, attack: object) -> bool:
        """Check whether an attack can legally target another unit.

        Args:
            actor: Acting unit. It must be alive.
            target: Candidate target unit. It must be alive, hostile, and not
                the acting unit itself.
            attack: Attack profile whose ``range`` must be a positive integer.
        """
        if target.id == actor.id or not target.alive or target.team == actor.team:
            return False
        return grid_distance(actor.tile_position, target.tile_position) <= attack.range


def _roll_damage(expression: str, rng: random.Random, critical: bool = False) -> DamageRoll:
    """Roll a simple dice expression of the form ``XdY+Z`` or ``XdY-Z``.

    Args:
        expression: Damage expression with positive dice count and dice sides.
            The optional modifier may be any signed integer.
        rng: Random source already seeded for deterministic replay.
        critical: When ``True``, double only the number of damage dice. The
            modifier is still added exactly once.
    """
    match = _DICE_RE.fullmatch(expression)
    if match is None:
        raise ValueError(f"Unsupported damage expression {expression}.")
    count = int(match.group("count"))
    sides = int(match.group("sides"))
    modifier = int(match.group("modifier") or 0)
    roll_count = count * 2 if critical else count
    dice_values = tuple(rng.randint(1, sides) for _ in range(roll_count))
    return DamageRoll(
        expression=expression,
        rolled_dice_count=roll_count,
        dice_sides=sides,
        dice_values=dice_values,
        modifier=modifier,
        total=sum(dice_values) + modifier,
        critical=critical,
    )


def _format_attack_resolution(resolution: ActionResolution) -> str:
    """Build a human-readable log message for an attack resolution.

    Args:
        resolution: Structured attack outcome with roll, AC, and damage data.
    """
    roll_summary = (
        f"d20 {resolution.raw_roll} + {resolution.attack_bonus} = {resolution.total_roll} "
        f"vs AC {resolution.target_ac}"
    )
    if resolution.outcome == "miss":
        if resolution.raw_roll == 1:
            return (
                f"{resolution.actor_id} missed {resolution.target_id} with {resolution.attack_name}: "
                f"natural 1, {roll_summary}."
            )
        return (
            f"{resolution.actor_id} missed {resolution.target_id} with {resolution.attack_name}: "
            f"{roll_summary}."
        )

    assert resolution.damage is not None
    damage_summary = _format_damage_roll(resolution.damage)
    if resolution.critical:
        return (
            f"{resolution.actor_id} critically hit {resolution.target_id} with {resolution.attack_name}: "
            f"natural 20, {roll_summary}; damage {damage_summary}; "
            f"HP {resolution.target_hp_before} -> {resolution.target_hp_after}."
        )
    return (
        f"{resolution.actor_id} hit {resolution.target_id} with {resolution.attack_name}: "
        f"{roll_summary}; damage {damage_summary}; "
        f"HP {resolution.target_hp_before} -> {resolution.target_hp_after}."
    )


def _format_damage_roll(damage_roll: DamageRoll) -> str:
    """Build a human-readable damage-roll breakdown string.

    Args:
        damage_roll: Structured damage roll with dice values and modifier.
    """
    dice_values = ", ".join(str(value) for value in damage_roll.dice_values)
    modifier_sign = "+" if damage_roll.modifier >= 0 else "-"
    modifier_value = abs(damage_roll.modifier)
    return (
        f"{damage_roll.rolled_dice_count}d{damage_roll.dice_sides}[{dice_values}] "
        f"{modifier_sign} {modifier_value} = {damage_roll.total}"
    )
