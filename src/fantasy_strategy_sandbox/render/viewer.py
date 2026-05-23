from __future__ import annotations

from dataclasses import dataclass

import pygame

from fantasy_strategy_sandbox.app.runtime import Command, GameRuntime
from fantasy_strategy_sandbox.combat.models import UnitState
from fantasy_strategy_sandbox.queries.movement import reachable_tiles
from fantasy_strategy_sandbox.render.projection import ProjectionConfig, sort_tiles_for_render, tile_polygon, unit_anchor
from fantasy_strategy_sandbox.world.models import Tile, TileCoord


@dataclass(frozen=True)
class ViewerConfig:
    screen_width: int = 1180
    screen_height: int = 720
    background_color: tuple[int, int, int] = (24, 28, 34)
    outline_color: tuple[int, int, int] = (14, 17, 20)
    panel_color: tuple[int, int, int] = (18, 21, 26)
    panel_text_color: tuple[int, int, int] = (229, 233, 240)
    hero_unit_color: tuple[int, int, int] = (89, 161, 255)
    enemy_unit_color: tuple[int, int, int] = (214, 96, 96)
    unit_outline_color: tuple[int, int, int] = (14, 17, 20)
    active_highlight_color: tuple[int, int, int] = (255, 215, 92)
    reachable_tile_color: tuple[int, int, int] = (120, 204, 255)
    selected_tile_color: tuple[int, int, int] = (255, 255, 255)
    blocked_tile_color: tuple[int, int, int] = (255, 134, 134)
    hud_width: int = 320
    hud_margin: int = 24
    font_size: int = 18
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
        self.projection_config = projection_config or _build_default_projection_config(self.viewer_config)
        self.selected_tile: TileCoord | None = None
        self.last_action_message = "Viewer ready."
        self.status_message = "Click a highlighted tile to move. Press Space to end the current turn."

    def run(self, max_frames: int | None = None) -> None:
        pygame.init()
        try:
            screen = pygame.display.set_mode((self.viewer_config.screen_width, self.viewer_config.screen_height))
            pygame.display.set_caption("Fantasy Strategy Sandbox - Tactical Viewer")
            font = pygame.font.SysFont("arial", self.viewer_config.font_size)
            clock = pygame.time.Clock()
            frame_count = 0
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        self._handle_keydown(event.key)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self._handle_left_click(event.pos)

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
        self._render_reachable_tiles(screen)
        self._render_units(screen)
        self._render_hud(screen, font)

    def _render_map(self, screen: pygame.Surface) -> None:
        # Keep the terrain pass intentionally lightweight so the first demo
        # stays aligned with the architecture goal of a low-cost viewer adapter.
        for tile in sort_tiles_for_render(list(self.runtime.game_map.tiles.values())):
            polygon = tile_polygon(tile, self.projection_config)
            color = _tile_color(tile)
            pygame.draw.polygon(screen, color, polygon)
            pygame.draw.polygon(screen, self.viewer_config.outline_color, polygon, width=2)

    def _render_reachable_tiles(self, screen: pygame.Surface) -> None:
        active_unit = self._active_unit()
        reachable = self._reachable_tiles_for_active_unit()
        for coord in reachable:
            if coord == active_unit.tile_position:
                continue
            polygon = tile_polygon(self.runtime.game_map.tile_at(coord), self.projection_config)
            pygame.draw.polygon(screen, self.viewer_config.reachable_tile_color, polygon, width=3)

        if self.selected_tile is not None and self.runtime.game_map.contains(self.selected_tile):
            polygon = tile_polygon(self.runtime.game_map.tile_at(self.selected_tile), self.projection_config)
            outline_color = (
                self.viewer_config.selected_tile_color
                if self.selected_tile in reachable
                else self.viewer_config.blocked_tile_color
            )
            pygame.draw.polygon(screen, outline_color, polygon, width=4)

    def _render_units(self, screen: pygame.Surface) -> None:
        state = self.runtime.current_state()
        active_unit_id = state.turn.active_unit_id
        units = sorted(
            state.units.values(),
            key=lambda unit: (unit.tile_position.x + unit.tile_position.y, unit.tile_position.x, unit.tile_position.y, unit.id),
        )

        # Render units after terrain so the viewer mirrors the authoritative
        # encounter state instead of inventing scene ownership in the renderer.
        for unit in units:
            tile = self.runtime.game_map.tile_at(unit.tile_position)
            anchor_x, anchor_y = unit_anchor(unit.tile_position, tile.height, self.projection_config)
            unit_color = _unit_color(unit, self.viewer_config)
            radius = max(12, self.projection_config.tile_height // 3)

            if unit.id == active_unit_id:
                pygame.draw.circle(screen, self.viewer_config.active_highlight_color, (anchor_x, anchor_y), radius + 8)

            pygame.draw.circle(screen, self.viewer_config.unit_outline_color, (anchor_x, anchor_y), radius + 2)
            pygame.draw.circle(screen, unit_color, (anchor_x, anchor_y), radius)

    def _render_hud(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        state = self.runtime.current_state()
        panel = self._hud_panel_rect()
        pygame.draw.rect(screen, self.viewer_config.panel_color, panel, border_radius=10)
        pygame.draw.rect(screen, self.viewer_config.outline_color, panel, width=2, border_radius=10)

        lines = [
            f"Encounter: {state.encounter_id}",
            f"Round: {state.turn.round_number}",
            f"Active unit: {state.turn.active_unit_id}",
            f"Status: {state.status}",
            f"Selected tile: {self.selected_tile if self.selected_tile is not None else 'none'}",
            f"Last action: {self.last_action_message}",
            f"Hint: {self.status_message}",
            "Controls: left click to select or move, Space to end turn.",
        ]

        wrapped_lines: list[str] = []
        max_text_width = panel.width - 36
        for line in lines:
            wrapped_lines.extend(_wrap_text(line, font, max_text_width))

        for index, line in enumerate(wrapped_lines):
            text_surface = font.render(line, True, self.viewer_config.panel_text_color)
            screen.blit(text_surface, (panel.x + 18, panel.y + 16 + index * (font.get_linesize() + 2)))

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_SPACE:
            self._end_turn()

    def _handle_left_click(self, position: tuple[int, int]) -> None:
        tile_coord = self._tile_at_screen_position(position)
        if tile_coord is None:
            self.status_message = "Click a visible tile to select a destination."
            return

        self.selected_tile = tile_coord
        active_unit = self._active_unit()
        reachable = self._reachable_tiles_for_active_unit()
        if tile_coord == active_unit.tile_position:
            self.status_message = "The active unit is already standing on that tile."
            return

        if tile_coord not in reachable:
            self.status_message = "That tile is not a valid destination for the active unit."
            return

        self._move_active_unit(tile_coord)

    def _move_active_unit(self, target: TileCoord) -> None:
        active_unit_id = self._active_unit().id
        try:
            self.runtime.execute(Command(type="move_unit", unit_id=active_unit_id, target={"x": target.x, "y": target.y}))
        except ValueError as exc:
            self.last_action_message = f"Move failed: {exc}"
            self.status_message = "Pick one of the highlighted tiles to move."
            return

        self.selected_tile = target
        self.last_action_message = f"{active_unit_id} moved to ({target.x}, {target.y})."
        self.status_message = "Move applied. Press Space to end the turn or click another highlighted tile."

    def _end_turn(self) -> None:
        active_unit_id = self._active_unit().id
        try:
            self.runtime.execute(Command(type="end_turn", unit_id=active_unit_id))
        except ValueError as exc:
            self.last_action_message = f"End turn failed: {exc}"
            self.status_message = "The active unit cannot end its turn right now."
            return

        new_active_unit = self._active_unit().id
        self.selected_tile = self._active_unit().tile_position
        self.last_action_message = f"{active_unit_id} ended its turn. {new_active_unit} is now active."
        self.status_message = "Select a highlighted tile to move the active unit."

    def _active_unit(self) -> UnitState:
        state = self.runtime.current_state()
        return state.units[state.turn.active_unit_id]

    def _reachable_tiles_for_active_unit(self) -> dict[TileCoord, int]:
        state = self.runtime.current_state()
        active_unit = self._active_unit()
        occupied = {unit.tile_position for unit in state.units.values() if unit.alive}
        return reachable_tiles(
            game_map=self.runtime.game_map,
            start=active_unit.tile_position,
            movement_budget=state.turn.remaining_movement,
            occupied=occupied,
        )

    def _tile_at_screen_position(self, position: tuple[int, int]) -> TileCoord | None:
        for tile in reversed(sort_tiles_for_render(list(self.runtime.game_map.tiles.values()))):
            if _point_in_polygon(position, tile_polygon(tile, self.projection_config)):
                return tile.coord
        return None

    def _hud_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.viewer_config.screen_width - self.viewer_config.hud_width - self.viewer_config.hud_margin,
            self.viewer_config.hud_margin,
            self.viewer_config.hud_width,
            self.viewer_config.screen_height - self.viewer_config.hud_margin * 2,
        )


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


def _point_in_polygon(point: tuple[int, int], polygon: list[tuple[int, int]]) -> bool:
    x, y = point
    inside = False
    for index in range(len(polygon)):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % len(polygon)]
        intersects = ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1)
        if intersects:
            inside = not inside
    return inside


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if font.size(candidate)[0] <= max_width:
            current_line = candidate
            continue
        lines.append(current_line)
        current_line = word
    lines.append(current_line)
    return lines


def _build_default_projection_config(viewer_config: ViewerConfig) -> ProjectionConfig:
    playable_width = viewer_config.screen_width - viewer_config.hud_width - viewer_config.hud_margin * 3
    origin_x = viewer_config.hud_margin + playable_width // 2
    return ProjectionConfig(origin_x=origin_x, origin_y=180)
