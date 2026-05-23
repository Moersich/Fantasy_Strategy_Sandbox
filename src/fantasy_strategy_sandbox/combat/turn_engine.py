from __future__ import annotations

import random
import re
from typing import Iterable

from fantasy_strategy_sandbox.combat.models import EncounterDefinition, EncounterState, TurnState, UnitDefinition, UnitState
from fantasy_strategy_sandbox.queries.movement import grid_distance, reachable_tiles
from fantasy_strategy_sandbox.world.models import GameMap, TileCoord

_DICE_RE = re.compile(r"^(?P<count>\d+)d(?P<sides>\d+)(?P<modifier>[+-]\d+)?$")


class TurnEngine:
    def start_encounter(self, game_map: GameMap, encounter_definition: EncounterDefinition) -> EncounterState:
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
        if state.status != "active":
            raise ValueError("Encounter is not active.")

        command_type = getattr(command, "type", None)
        if not command_type:
            raise ValueError("Command requires a type.")

        if command_type == "move_unit":
            self._move_unit(state, game_map, command)
        elif command_type == "attack_target":
            self._attack_target(state, command)
        elif command_type == "dash":
            self._dash(state, command)
        elif command_type == "end_turn":
            self._require_active_unit(state, getattr(command, "unit_id"))
            self._end_turn(state)
        else:
            raise ValueError(f"Unsupported command type {command_type}.")

        self._update_winner(state)
        return state

    def _instantiate_units(self, game_map: GameMap, unit_definitions: Iterable[UnitDefinition]) -> dict[str, UnitState]:
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
        rng = random.Random(seed)
        initiative_entries = []
        for definition in unit_definitions:
            roll = rng.randint(1, 20) + definition.initiative_bonus
            initiative_entries.append((roll, definition.initiative_bonus, definition.id))
        initiative_entries.sort(key=lambda entry: (-entry[0], -entry[1], entry[2]))
        return [entry[2] for entry in initiative_entries]

    def _move_unit(self, state: EncounterState, game_map: GameMap, command: object) -> None:
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

    def _attack_target(self, state: EncounterState, command: object) -> None:
        actor = self._require_active_unit(state, getattr(command, "unit_id"))
        if not state.turn.action_available:
            raise ValueError(f"{actor.id} has already spent its action.")
        target_id = getattr(command, "target_id")
        if not target_id:
            raise ValueError("attack_target requires a target_id.")
        if target_id not in state.units:
            raise ValueError(f"Unknown target unit {target_id}.")
        if target_id == actor.id:
            raise ValueError(f"{actor.id} cannot target itself.")

        target = state.units[target_id]
        if not target.alive:
            raise ValueError(f"Target {target.id} is already defeated.")

        attack = actor.attacks[0]
        if grid_distance(actor.tile_position, target.tile_position) > attack.range:
            raise ValueError(f"Target {target.id} is out of range for {actor.id}.")

        rng = random.Random(self._command_seed(state))
        attack_roll = rng.randint(1, 20) + attack.attack_bonus
        if attack_roll >= target.ac:
            damage = _roll_damage(attack.damage, rng)
            target.hp = max(0, target.hp - damage)
            target.alive = target.hp > 0
            state.log.append(f"{actor.id} hit {target.id} for {damage} damage.")
        else:
            state.log.append(f"{actor.id} missed {target.id}.")

        state.turn.action_available = False

    def _dash(self, state: EncounterState, command: object) -> None:
        actor = self._require_active_unit(state, getattr(command, "unit_id"))
        if not state.turn.action_available:
            raise ValueError(f"{actor.id} has already spent its action.")
        state.turn.remaining_movement += actor.speed
        state.turn.action_available = False
        state.log.append(f"{actor.id} used Dash and now has {state.turn.remaining_movement} movement.")

    def _end_turn(self, state: EncounterState) -> None:
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
        living_teams = {unit.team for unit in state.units.values() if unit.alive}
        if len(living_teams) == 1:
            state.status = "ended"
            state.winner_team = next(iter(living_teams))
            state.log.append(f"Encounter ended. Winner: {state.winner_team}.")

    def _require_active_unit(self, state: EncounterState, unit_id: str | None) -> UnitState:
        if unit_id is None:
            raise ValueError("Command requires a unit_id.")
        if state.turn.active_unit_id != unit_id:
            raise ValueError(f"{unit_id} is not the active unit.")
        return state.units[unit_id]

    def _command_seed(self, state: EncounterState) -> int:
        return state.turn.initiative_seed + state.turn.round_number * 100 + state.turn.turn_index


def _roll_damage(expression: str, rng: random.Random) -> int:
    match = _DICE_RE.fullmatch(expression)
    if match is None:
        raise ValueError(f"Unsupported damage expression {expression}.")
    count = int(match.group("count"))
    sides = int(match.group("sides"))
    modifier = int(match.group("modifier") or 0)
    return sum(rng.randint(1, sides) for _ in range(count)) + modifier
