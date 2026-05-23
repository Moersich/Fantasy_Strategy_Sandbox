from __future__ import annotations

from dataclasses import dataclass

import pygame

from fantasy_strategy_sandbox.app.runtime import GameRuntime
from fantasy_strategy_sandbox.render.projection import ProjectionConfig, sort_tiles_for_render, tile_polygon
from fantasy_strategy_sandbox.world.models import Tile


@dataclass(frozen=True)
class ViewerConfig:
    screen_width: int = 960
    screen_height: int = 720
    background_color: tuple[int, int, int] = (24, 28, 34)
    outline_color: tuple[int, int, int] = (14, 17, 20)
    fps: int = 60


class TacticalViewer:
    def __init__(
        self,
        runtime: GameRuntime,
        viewer_config: ViewerConfig | None = None,
        projection_config: ProjectionConfig | None = None,
    ) -> None:
        self.runtime = runtime
        self.viewer_config = viewer_config or ViewerConfig()
        self.projection_config = projection_config or ProjectionConfig()

    def run(self, max_frames: int | None = None) -> None:
        pygame.init()
        try:
            screen = pygame.display.set_mode((self.viewer_config.screen_width, self.viewer_config.screen_height))
            pygame.display.set_caption("Fantasy Strategy Sandbox - Tactical Viewer")
            clock = pygame.time.Clock()
            frame_count = 0
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                self._render_frame(screen)
                pygame.display.flip()
                clock.tick(self.viewer_config.fps)

                frame_count += 1
                if max_frames is not None and frame_count >= max_frames:
                    running = False
        finally:
            pygame.quit()

    def _render_frame(self, screen: pygame.Surface) -> None:
        screen.fill(self.viewer_config.background_color)
        self._render_map(screen)

    def _render_map(self, screen: pygame.Surface) -> None:
        # Use a simple low-cost isometric projection here to match the
        # architecture goal of lightweight visuals in the first demo slice.
        for tile in sort_tiles_for_render(list(self.runtime.game_map.tiles.values())):
            color = _tile_color(tile)
            pygame.draw.polygon(screen, color, tile_polygon(tile, self.projection_config))
            pygame.draw.polygon(
                screen,
                self.viewer_config.outline_color,
                tile_polygon(tile, self.projection_config),
                width=2,
            )


def _tile_color(tile: Tile) -> tuple[int, int, int]:
    if tile.blocks_movement:
        return (92, 72, 72)
    if tile.surface_type == "ground":
        return (98, 144, 98)
    return (110, 110, 130)
