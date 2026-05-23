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
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        target_coord = TileCoord(3, 1)
        target = project_tile(target_coord, 0, viewer.projection_config)

        viewer._handle_left_click(target)

        self.assertEqual(runtime.current_state().units["goblin_1"].tile_position, target_coord)
        self.assertIn("moved to", viewer.last_action_message)

    def test_space_ends_turn_and_updates_feedback(self) -> None:
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)

        viewer._handle_keydown(pygame.K_SPACE)

        self.assertEqual(runtime.current_state().turn.active_unit_id, "goblin_2")
        self.assertIn("ended its turn", viewer.last_action_message)

    def test_clicking_invalid_tile_sets_status_message(self) -> None:
        runtime = create_training_yard_runtime()
        viewer = TacticalViewer(runtime)
        target = project_tile(runtime.game_map.tile_at(runtime.game_map.spawns["heroes-a"]).coord, 0, viewer.projection_config)

        viewer._handle_left_click(target)

        self.assertEqual(runtime.current_state().units["goblin_1"].tile_position, runtime.game_map.spawns["goblins-a"])
        self.assertIn("not a valid destination", viewer.status_message)

    def test_hud_panel_stays_right_of_projected_map(self) -> None:
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
