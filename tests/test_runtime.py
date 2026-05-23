import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.combat.models import AttackDefinition, EncounterDefinition, UnitDefinition
from fantasy_strategy_sandbox.app.runtime import Command, GameRuntime
from fantasy_strategy_sandbox.world.models import GameMap, Tile, TileCoord


def runtime() -> GameRuntime:
    """Create the standard training-yard runtime for runtime tests."""
    game_runtime = GameRuntime.from_files(
        "data/maps/training-yard.json",
        "data/encounters/training-yard-skirmish.json",
    )
    game_runtime.start_encounter()
    return game_runtime


def duel_runtime(
    initiative_seed: int = 0,
    hero_attack_bonus: int = 100,
    hero_damage: str = "1d1+0",
    hero_range: int = 1,
    goblin_hp: int = 1,
    goblin_ac: int = 1,
) -> GameRuntime:
    """Create a minimal two-unit runtime with controllable combat values.

    Args:
        initiative_seed: Deterministic initiative seed. Any integer is valid.
        hero_attack_bonus: Attack bonus applied to the hero's only attack.
        hero_damage: Damage expression understood by the combat core.
        hero_range: Attack range in tiles. Expected range is ``>= 1``.
        goblin_hp: Goblin max and current hit points. Expected range is ``>= 1``.
        goblin_ac: Goblin armor class. Expected range is ``>= 1``.
    """
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
        initiative_seed=initiative_seed,
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
                attacks=[AttackDefinition(name="Sure strike", attack_bonus=hero_attack_bonus, damage=hero_damage, range=hero_range)],
            ),
            UnitDefinition(
                id="goblin_1",
                name="Goblin",
                team="goblins",
                spawn_id="enemy",
                max_hp=goblin_hp,
                hp=goblin_hp,
                ac=goblin_ac,
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
        """Verify seeded initiative produces stable startup order."""
        game_runtime = runtime()

        self.assertIsNotNone(game_runtime.encounter_state)
        self.assertEqual(
            game_runtime.encounter_state.turn.initiative_order,
            ["goblin_1", "goblin_2", "fighter_1", "rogue_1"],
        )
        self.assertEqual(game_runtime.encounter_state.turn.active_unit_id, "goblin_1")
        self.assertEqual(game_runtime.encounter_state.turn.round_number, 1)

    def test_move_command_updates_position_and_movement_budget(self) -> None:
        """Verify a move command changes tile position and movement budget."""
        game_runtime = runtime()

        game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 3, "y": 1}))

        goblin = game_runtime.encounter_state.units["goblin_1"]
        self.assertEqual((goblin.tile_position.x, goblin.tile_position.y), (3, 1))
        self.assertEqual(game_runtime.encounter_state.turn.remaining_movement, 5)

    def test_dash_consumes_action_and_adds_movement(self) -> None:
        """Verify Dash spends the action and increases movement."""
        game_runtime = runtime()

        game_runtime.execute(Command(type="dash", unit_id="goblin_1"))

        self.assertEqual(game_runtime.encounter_state.turn.remaining_movement, 12)
        self.assertFalse(game_runtime.encounter_state.turn.action_available)

    def test_end_turn_advances_to_next_unit(self) -> None:
        """Verify ending a turn advances initiative without changing rounds."""
        game_runtime = runtime()

        game_runtime.execute(Command(type="end_turn", unit_id="goblin_1"))

        self.assertEqual(game_runtime.encounter_state.turn.active_unit_id, "goblin_2")
        self.assertEqual(game_runtime.encounter_state.turn.round_number, 1)

    def test_attack_consumes_action_and_applies_damage(self) -> None:
        """Verify Attack Action deals damage and spends the action."""
        game_runtime = runtime()
        game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 2, "y": 1}))

        game_runtime.execute(Command(type="use_action", unit_id="goblin_1", action_id="attack", target_id="fighter_1"))

        fighter = game_runtime.encounter_state.units["fighter_1"]
        resolution = game_runtime.encounter_state.last_resolution
        self.assertLess(fighter.hp, fighter.max_hp)
        self.assertFalse(game_runtime.encounter_state.turn.action_available)
        self.assertIsNotNone(resolution)
        self.assertEqual(resolution.raw_roll, 19)
        self.assertEqual(resolution.total_roll, 23)
        self.assertTrue(resolution.hit)
        self.assertIsNotNone(resolution.damage)
        self.assertIn("d20 19 + 4 = 23 vs AC 16", game_runtime.encounter_state.log[-1])

    def test_end_turn_wraps_to_next_round_after_last_unit(self) -> None:
        """Verify initiative wrap increments the round counter."""
        game_runtime = runtime()

        game_runtime.execute(Command(type="end_turn", unit_id="goblin_1"))
        game_runtime.execute(Command(type="end_turn", unit_id="goblin_2"))
        game_runtime.execute(Command(type="end_turn", unit_id="fighter_1"))
        game_runtime.execute(Command(type="end_turn", unit_id="rogue_1"))

        self.assertEqual(game_runtime.encounter_state.turn.active_unit_id, "goblin_1")
        self.assertEqual(game_runtime.encounter_state.turn.round_number, 2)

    def test_execute_rejects_wrong_active_unit(self) -> None:
        """Verify commands are rejected for non-active units."""
        game_runtime = runtime()

        with self.assertRaisesRegex(ValueError, "fighter_1 is not the active unit"):
            game_runtime.execute(Command(type="end_turn", unit_id="fighter_1"))

    def test_move_unit_rejects_target_without_complete_coordinates(self) -> None:
        """Verify movement requires integer x/y tile coordinates."""
        game_runtime = runtime()

        with self.assertRaisesRegex(ValueError, "move_unit target must include integer x and y coordinates"):
            game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 3}))

    def test_attack_target_rejects_self_target(self) -> None:
        """Verify attack commands reject self-targeting."""
        game_runtime = runtime()

        with self.assertRaisesRegex(ValueError, "cannot target itself"):
            game_runtime.execute(Command(type="attack_target", unit_id="goblin_1", target_id="goblin_1"))

    def test_available_actions_and_legal_targets_follow_active_unit_state(self) -> None:
        """Verify action metadata and legal targets track current state."""
        game_runtime = runtime()

        actions = game_runtime.available_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].id, "attack")
        self.assertEqual(actions[0].attack_name, "Scimitar")
        self.assertEqual(actions[0].range, 1)
        self.assertEqual(game_runtime.legal_targets_for_action("attack"), [])

        game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 2, "y": 1}))

        self.assertEqual(game_runtime.legal_targets_for_action("attack"), ["fighter_1", "rogue_1"])

    def test_summary_exposes_available_actions(self) -> None:
        """Verify the runtime summary exports action metadata."""
        game_runtime = runtime()

        summary = game_runtime.summary()

        self.assertEqual(summary["available_actions"][0]["id"], "attack")
        self.assertEqual(summary["available_actions"][0]["attack_name"], "Scimitar")
        self.assertIsNone(summary["last_resolution"])

    def test_natural_one_is_automatic_miss(self) -> None:
        """Verify a natural 1 misses regardless of bonuses."""
        game_runtime = duel_runtime(initiative_seed=4, hero_attack_bonus=100, hero_damage="1d1+2", goblin_hp=5, goblin_ac=1)

        game_runtime.execute(Command(type="use_action", unit_id="hero_1", action_id="attack", target_id="goblin_1"))

        goblin = game_runtime.encounter_state.units["goblin_1"]
        resolution = game_runtime.encounter_state.last_resolution
        self.assertEqual(goblin.hp, 5)
        self.assertIsNotNone(resolution)
        self.assertEqual(resolution.raw_roll, 1)
        self.assertFalse(resolution.hit)
        self.assertIsNone(resolution.damage)
        self.assertIn("natural 1", game_runtime.encounter_state.log[-1])

    def test_natural_twenty_is_critical_hit(self) -> None:
        """Verify a natural 20 crits regardless of target AC."""
        game_runtime = duel_runtime(initiative_seed=16, hero_attack_bonus=0, hero_damage="1d1+2", goblin_hp=5, goblin_ac=99)

        game_runtime.execute(Command(type="use_action", unit_id="hero_1", action_id="attack", target_id="goblin_1"))

        goblin = game_runtime.encounter_state.units["goblin_1"]
        resolution = game_runtime.encounter_state.last_resolution
        self.assertEqual(goblin.hp, 1)
        self.assertIsNotNone(resolution)
        self.assertTrue(resolution.critical)
        self.assertEqual(resolution.raw_roll, 20)
        self.assertEqual(resolution.damage.rolled_dice_count, 2)
        self.assertIn("natural 20", game_runtime.encounter_state.log[-1])

    def test_summary_exposes_last_resolution_details(self) -> None:
        """Verify the runtime summary exports structured roll resolution."""
        game_runtime = runtime()
        game_runtime.execute(Command(type="move_unit", unit_id="goblin_1", target={"x": 2, "y": 1}))
        game_runtime.execute(Command(type="use_action", unit_id="goblin_1", action_id="attack", target_id="fighter_1"))

        summary = game_runtime.summary()

        self.assertEqual(summary["last_resolution"]["raw_roll"], 19)
        self.assertEqual(summary["last_resolution"]["outcome"], "hit")
        self.assertEqual(summary["last_resolution"]["damage"]["rolled_dice_count"], 1)

    def test_attack_can_end_encounter_and_set_winner(self) -> None:
        """Verify lethal attack resolution ends the encounter."""
        game_runtime = duel_runtime()

        game_runtime.execute(Command(type="use_action", unit_id="hero_1", action_id="attack", target_id="goblin_1"))

        self.assertEqual(game_runtime.encounter_state.status, "ended")
        self.assertEqual(game_runtime.encounter_state.winner_team, "heroes")


if __name__ == "__main__":
    unittest.main()
