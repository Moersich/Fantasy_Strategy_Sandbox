from __future__ import annotations

from dataclasses import dataclass

import pygame

from fantasy_strategy_sandbox.app.runtime import GameRuntime
from fantasy_strategy_sandbox.combat.models import UnitState
from fantasy_strategy_sandbox.render.projection import ProjectionConfig, sort_tiles_for_render, tile_polygon, unit_anchor
from fantasy_strategy_sandbox.world.models import Tile


@dataclass(frozen=True)
class ViewerConfig:
    screen_width: int = 960
    screen_height: int = 720
    background_color: tuple[int, int, int] = (24, 28, 34)
    outline_color: tuple[int, int, int] = (14, 17, 20)
    panel_color: tuple[int, int, int] = (18, 21, 26)
    panel_text_color: tuple[int, int, int] = (229, 233, 240)
    hero_unit_color: tuple[int, int, int] = (89, 161, 255)
    enemy_unit_color: tuple[int, int, int] = (214, 96, 96)
    unit_outline_color: tuple[int, int, int] = (14, 17, 20)
    active_highlight_color: tuple[int, int, int] = (255, 215, 92)
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
            font = pygame.font.SysFont("arial", 22)
            clock = pygame.time.Clock()
            frame_count = 0
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                self._render_frame(screen, font)
                pygame.display.flip()
                clock.tick(self.viewer_config.fps)

                frame_count += 1
                if max_frames is not None and frame_count >= max_frames:
                    running = False
        finally:
            pygame.quit()

    def _render_frame(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        screen.fill(self.viewer_config.background_color)
        self._render_map(screen)
        self._render_units(screen)
        self._render_hud(screen, font)

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

    def _render_units(self, screen: pygame.Surface) -> None:
        state = self.runtime.current_state()
        active_unit_id = state.turn.active_unit_id
        units = sorted(
            state.units.values(),
            key=lambda unit: (unit.tile_position.x + unit.tile_position.y, unit.tile_position.x, unit.tile_position.y, unit.id),
        )

        # Render units after terrain so the viewer mirrors the authoritative
        # encounter state instead of inventing its own scene ordering rules.
        for unit in units:
            tile = self.runtime.game_map.tile_at(unit.tile_position)
            anchor_x, anchor_y = unit_anchor(unit.tile_position, tile.height, self.projection_config)
            unit_color = _unit_color(unit, self.viewer_config)
            radius = max(12, self.projection_config.tile_height // 3)

            if unit.id == active_unit_id:
                pygame.draw.circle(
                    screen,
                    self.viewer_config.active_highlight_color,
                    (anchor_x, anchor_y),
                    radius + 8,
                )

            pygame.draw.circle(screen, self.viewer_config.unit_outline_color, (anchor_x, anchor_y), radius + 2)
            pygame.draw.circle(screen, unit_color, (anchor_x, anchor_y), radius)

    def _render_hud(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        state = self.runtime.current_state()
        panel = pygame.Rect(24, 24, 300, 132)
        pygame.draw.rect(screen, self.viewer_config.panel_color, panel, border_radius=10)
        pygame.draw.rect(screen, self.viewer_config.outline_color, panel, width=2, border_radius=10)

        lines = (
            f"Encounter: {state.encounter_id}",
            f"Round: {state.turn.round_number}",
            f"Active unit: {state.turn.active_unit_id}",
            f"Status: {state.status}",
        )
        for index, line in enumerate(lines):
            text_surface = font.render(line, True, self.viewer_config.panel_text_color)
            screen.blit(text_surface, (42, 40 + index * 24))


def _tile_color(tile: Tile) -> tuple[int, int, int]:
    if tile.blocks_movement:
        return (92, 72, 72)
    if tile.surface_type == "ground":
        return (98, 144, 98)
    return (110, 110, 130)


def _unit_color(unit: UnitState, config: ViewerConfig) -> tuple[int, int, int]:
    if unit.team == "heroes":
        return config.hero_unit_color
    return config.enemy_unit_color
