import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.app.runtime import Command, GameRuntime


def runtime() -> GameRuntime:
    game_runtime = GameRuntime.from_files(
        "data/maps/training-yard.json",
        "data/encounters/training-yard-skirmish.json",
    )
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


if __name__ == "__main__":
    unittest.main()
