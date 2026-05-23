import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from fantasy_strategy_sandbox.app.demo import create_training_yard_runtime
from fantasy_strategy_sandbox.render.projection import project_tile, tile_polygon
from fantasy_strategy_sandbox.render.viewer import TacticalViewer, ViewerConfig
from fantasy_strategy_sandbox.world.models import TileCoord


class ViewerStateVisualizationTests(unittest.TestCase):
    def test_viewer_renders_combat_state_without_runtime_errors(self) -> None:
        """Verify a frame renders successfully onto an off-screen surface."""
        pygame.init()
        try:
            runtime = create_training_yard_runtime()
            viewer = TacticalViewer(runtime, viewer_config=ViewerConfig(screen_width=640, screen_height=480))
            screen = pygame.Surface((640, 480))
            font = pygame.font.SysFont("arial", 18)

            viewer._render_frame(screen, font)

            panel = viewer._hud_panel_rect()
            self.assertNotEqual(screen.get_at((panel.x + 10, panel.y + 10)), pygame.Color(24, 28, 34, 255))
        finally:
            pygame.quit()

    def test_clicking_reachable_tile_moves_active_unit(self) -> None:
        """Verify clicking a reachable tile submits a move command."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        target_coord = TileCoord(3, 1)
        target = project_tile(target_coord, 0, viewer.projection_config)

        viewer._handle_left_click(target)

        self.assertEqual(runtime.current_state().units["goblin_1"].tile_position, target_coord)
        self.assertIn("moved to", viewer.last_action_message)

    def test_space_ends_turn_and_updates_feedback(self) -> None:
        """Verify the Space key ends the active turn."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)

        viewer._handle_keydown(pygame.K_SPACE)

        self.assertEqual(runtime.current_state().turn.active_unit_id, "goblin_2")
        self.assertIn("ended its turn", viewer.last_action_message)

    def test_attack_mode_can_hit_target_in_range(self) -> None:
        """Verify attack mode can resolve Attack Action against a legal target."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        move_target = project_tile(TileCoord(2, 1), 0, viewer.projection_config)
        attack_target = project_tile(runtime.game_map.spawns["heroes-a"], 0, viewer.projection_config)

        viewer._handle_left_click(move_target)
        viewer._handle_keydown(pygame.K_a)
        viewer._handle_left_click(attack_target)

        self.assertLess(runtime.current_state().units["fighter_1"].hp, runtime.current_state().units["fighter_1"].max_hp)
        self.assertIn("d20 19 + 4 = 23", viewer.last_action_message)
        self.assertEqual(viewer.interaction_mode, "move")

    def test_hud_sections_show_latest_roll_breakdown(self) -> None:
        """Verify the HUD groups state into readable sections with roll detail."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        move_target = project_tile(TileCoord(2, 1), 0, viewer.projection_config)
        attack_target = project_tile(runtime.game_map.spawns["heroes-a"], 0, viewer.projection_config)

        viewer._handle_left_click(move_target)
        viewer._handle_keydown(pygame.K_a)
        viewer._handle_left_click(attack_target)

        sections = dict(viewer._hud_sections())

        self.assertIn("TURN", sections)
        self.assertIn("LAST ROLL", sections)
        self.assertIn("Roll: d20 19 + 4 = 23 vs AC 16", sections["LAST ROLL"])
        self.assertTrue(any("Damage:" in line for line in sections["LAST ROLL"]))

    def test_clicking_invalid_tile_sets_status_message(self) -> None:
        """Verify invalid movement clicks only update viewer feedback."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        target = project_tile(runtime.game_map.tile_at(runtime.game_map.spawns["heroes-a"]).coord, 0, viewer.projection_config)

        viewer._handle_left_click(target)

        self.assertEqual(runtime.current_state().units["goblin_1"].tile_position, runtime.game_map.spawns["goblins-a"])
        self.assertIn("not a valid destination", viewer.status_message)

    def test_attack_mode_reports_invalid_target(self) -> None:
        """Verify attack mode reports illegal target selections."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        target = project_tile(runtime.game_map.tile_at(runtime.game_map.spawns["heroes-a"]).coord, 0, viewer.projection_config)

        viewer._handle_keydown(pygame.K_a)
        viewer._handle_left_click(target)

        self.assertIn("not a valid attack target", viewer.status_message)

    def test_hud_panel_stays_right_of_projected_map(self) -> None:
        """Verify HUD layout stays outside the projected play area."""
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)

        max_map_x = max(
            point[0]
            for tile in runtime.game_map.tiles.values()
            for point in tile_polygon(tile, viewer.projection_config)
        )

        self.assertGreater(viewer._hud_panel_rect().left, max_map_x)


if __name__ == "__main__":
    unittest.main()
