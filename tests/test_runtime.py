import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.combat.models import AttackDefinition, EncounterDefinition, UnitDefinition
from fantasy_strategy_sandbox.app.runtime import Command, GameRuntime
from fantasy_strategy_sandbox.world.models import GameMap, Tile, TileCoord


def runtime() -> GameRuntime:
    game_runtime = GameRuntime.from_files(
        "data/maps/training-yard.json",
        "data/encounters/training-yard-skirmish.json",
    )
    game_runtime.start_encounter()
    return game_runtime


def duel_runtime() -> GameRuntime:
    game_map = GameMap(
        map_id="duel-map",
        version=1,
        width=2,
        height=1,
        tiles={
            TileCoord(0, 0): Tile(TileCoord(0, 0), height=0, surface_type="ground", movement_cost=1, blocks_movement=False, blocks_los=False, cover_type="none"),
            TileCoord(1, 0): Tile(TileCoord(1, 0), height=0, surface_type="ground", movement_cost=1, blocks_movement=False, blocks_los=False, cover_type="none"),
        },
        spawns={"hero": TileCoord(0, 0), "enemy": TileCoord(1, 0)},
    )
    encounter_definition = EncounterDefinition(
        encounter_id="duel",
        map_id="duel-map",
        initiative_seed=0,
        units=[
            UnitDefinition(
                id="hero_1",
                name="Hero",
                team="heroes",
                spawn_id="hero",
                max_hp=10,
                hp=10,
                ac=15,
                speed=6,
                initiative_bonus=100,
                attacks=[AttackDefinition(name="Sure strike", attack_bonus=100, damage="1d1+0", range=1)],
            ),
            UnitDefinition(
                id="goblin_1",
                name="Goblin",
                team="goblins",
                spawn_id="enemy",
                max_hp=1,
                hp=1,
                ac=1,
                speed=6,
                initiative_bonus=0,
                attacks=[AttackDefinition(name="Dagger", attack_bonus=0, damage="1d1+0", range=1)],
            ),
        ],
    )
    game_runtime = GameRuntime(game_map=game_map, encounter_definition=encounter_definition)
    game_runtime.start_encounter()
    return game_runtime


class RuntimeTests(unittest.TestCase):
    def test_start_encounter_sets_deterministic_turn_order(self) -> None:
        game_runtime = runtime()

        self.assertIsNotNone(game_runtime.encounter_state)
        self.assertEqual(
            game_runtime.encounter_state.turn.initiative_order,
            ["goblin_1", "goblin_2", "fighter_1", "rogue_1"],
        )
        self.assertEqual(game_runtime.encounter_state.turn.active_unit_id, "goblin_1")
        self.assertEqual(game_runtime.encounter_state.turn.round_number, 1)

    def test_move_command_updates_position_and_movement_budget(self) -> None:
        game_runtime = runtime()

        game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 3, "y": 1}))

        goblin = game_runtime.encounter_state.units["goblin_1"]
        self.assertEqual((goblin.tile_position.x, goblin.tile_position.y), (3, 1))
        self.assertEqual(game_runtime.encounter_state.turn.remaining_movement, 5)

    def test_dash_consumes_action_and_adds_movement(self) -> None:
        game_runtime = runtime()

        game_runtime.execute(Command(type="dash", unit_id="goblin_1"))

        self.assertEqual(game_runtime.encounter_state.turn.remaining_movement, 12)
        self.assertFalse(game_runtime.encounter_state.turn.action_available)

    def test_end_turn_advances_to_next_unit(self) -> None:
        game_runtime = runtime()

        game_runtime.execute(Command(type="end_turn", unit_id="goblin_1"))

        self.assertEqual(game_runtime.encounter_state.turn.active_unit_id, "goblin_2")
        self.assertEqual(game_runtime.encounter_state.turn.round_number, 1)

    def test_attack_consumes_action_and_applies_damage(self) -> None:
        game_runtime = runtime()
        game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 2, "y": 1}))

        game_runtime.execute(Command(type="attack_target", unit_id="goblin_1", target_id="fighter_1"))

        fighter = game_runtime.encounter_state.units["fighter_1"]
        self.assertLess(fighter.hp, fighter.max_hp)
        self.assertFalse(game_runtime.encounter_state.turn.action_available)

    def test_end_turn_wraps_to_next_round_after_last_unit(self) -> None:
        game_runtime = runtime()

        game_runtime.execute(Command(type="end_turn", unit_id="goblin_1"))
        game_runtime.execute(Command(type="end_turn", unit_id="goblin_2"))
        game_runtime.execute(Command(type="end_turn", unit_id="fighter_1"))
        game_runtime.execute(Command(type="end_turn", unit_id="rogue_1"))

        self.assertEqual(game_runtime.encounter_state.turn.active_unit_id, "goblin_1")
        self.assertEqual(game_runtime.encounter_state.turn.round_number, 2)

    def test_execute_rejects_wrong_active_unit(self) -> None:
        game_runtime = runtime()

        with self.assertRaisesRegex(ValueError, "fighter_1 is not the active unit"):
            game_runtime.execute(Command(type="end_turn", unit_id="fighter_1"))

    def test_move_unit_rejects_target_without_complete_coordinates(self) -> None:
        game_runtime = runtime()

        with self.assertRaisesRegex(ValueError, "move_unit target must include integer x and y coordinates"):
            game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 3}))

    def test_attack_target_rejects_self_target(self) -> None:
        game_runtime = runtime()

        with self.assertRaisesRegex(ValueError, "cannot target itself"):
            game_runtime.execute(Command(type="attack_target", unit_id="goblin_1", target_id="goblin_1"))

    def test_attack_can_end_encounter_and_set_winner(self) -> None:
        game_runtime = duel_runtime()

        game_runtime.execute(Command(type="attack_target", unit_id="hero_1", target_id="goblin_1"))

        self.assertEqual(game_runtime.encounter_state.status, "ended")
        self.assertEqual(game_runtime.encounter_state.winner_team, "heroes")


if __name__ == "__main__":
    unittest.main()
