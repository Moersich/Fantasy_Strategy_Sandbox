import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from fantasy_strategy_sandbox.app.demo import create_training_yard_runtime
from fantasy_strategy_sandbox.render.viewer import TacticalViewer, ViewerConfig


class ViewerStateVisualizationTests(unittest.TestCase):
    def test_viewer_renders_combat_state_without_runtime_errors(self) -> None:
        pygame.init()
        try:
            runtime = create_training_yard_runtime()
            viewer = TacticalViewer(runtime, viewer_config=ViewerConfig(screen_width=640, screen_height=480))
            screen = pygame.Surface((640, 480))
            font = pygame.font.SysFont("arial", 18)

            viewer._render_frame(screen, font)

            self.assertNotEqual(screen.get_at((42, 40)), pygame.Color(24, 28, 34, 255))
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
