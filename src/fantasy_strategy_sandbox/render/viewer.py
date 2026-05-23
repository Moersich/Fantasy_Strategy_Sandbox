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
    attackable_tile_color: tuple[int, int, int] = (255, 134, 134)
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
        """Create a viewer adapter around the gameplay runtime.

        Args:
            runtime: Started or startable gameplay runtime whose state is the
                sole authority for combat.
            viewer_config: Optional visual configuration. Screen dimensions,
                font size, HUD width, and FPS should all be positive integers.
            projection_config: Optional projection constants. When omitted, a
                default configuration derived from ``viewer_config`` is used.
        """
        self.runtime = runtime
        self.viewer_config = viewer_config or ViewerConfig()
        self.projection_config = projection_config or _build_default_projection_config(self.viewer_config)
        self.selected_tile: TileCoord | None = None
        self.interaction_mode = "move"
        self.last_action_message = "Viewer ready."
        self.status_message = "Click a highlighted tile to move. Press A to attack. Press Space to end the current turn."

    def run(self, max_frames: int | None = None) -> None:
        """Open the Pygame window and process events until exit.

        Args:
            max_frames: Optional frame limit for smoke tests. ``None`` runs
                until the user closes the window. Practical values are integers
                ``>= 1``.
        """
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
        """Render one complete viewer frame.

        Args:
            screen: Destination surface whose size should match the configured
                screen width and height.
            font: Font used for HUD text. Its size should be readable inside the
                configured HUD width.
        """
        screen.fill(self.viewer_config.background_color)
        self._render_map(screen)
        self._render_reachable_tiles(screen)
        self._render_attack_targets(screen)
        self._render_units(screen)
        self._render_hud(screen, font)

    def _render_map(self, screen: pygame.Surface) -> None:
        """Render terrain tiles in painter's-order depth."""
        # Keep the terrain pass intentionally lightweight so the first demo
        # stays aligned with the architecture goal of a low-cost viewer adapter.
        for tile in sort_tiles_for_render(list(self.runtime.game_map.tiles.values())):
            polygon = tile_polygon(tile, self.projection_config)
            color = _tile_color(tile)
            pygame.draw.polygon(screen, color, polygon)
            pygame.draw.polygon(screen, self.viewer_config.outline_color, polygon, width=2)

    def _render_reachable_tiles(self, screen: pygame.Surface) -> None:
        """Draw movement overlays for the active unit."""
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

    def _render_attack_targets(self, screen: pygame.Surface) -> None:
        """Draw overlays for currently legal attack targets in attack mode."""
        if self.interaction_mode != "attack":
            return
        for unit in self._attackable_units().values():
            polygon = tile_polygon(self.runtime.game_map.tile_at(unit.tile_position), self.projection_config)
            pygame.draw.polygon(screen, self.viewer_config.attackable_tile_color, polygon, width=4)

    def _render_units(self, screen: pygame.Surface) -> None:
        """Render unit markers and the active-unit highlight."""
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
        """Render the right-hand HUD with state and control hints.

        Args:
            screen: Destination surface that already contains map and unit
                rendering.
            font: Font used to render wrapped HUD text.
        """
        state = self.runtime.current_state()
        panel = self._hud_panel_rect()
        pygame.draw.rect(screen, self.viewer_config.panel_color, panel, border_radius=10)
        pygame.draw.rect(screen, self.viewer_config.outline_color, panel, width=2, border_radius=10)
        max_text_width = panel.width - 36
        cursor_y = panel.y + 16
        for title, lines in self._hud_sections():
            title_surface = font.render(title, True, self.viewer_config.active_highlight_color)
            screen.blit(title_surface, (panel.x + 18, cursor_y))
            cursor_y += font.get_linesize() + 2

            for line in lines:
                for wrapped_line in _wrap_text(line, font, max_text_width):
                    text_surface = font.render(wrapped_line, True, self.viewer_config.panel_text_color)
                    screen.blit(text_surface, (panel.x + 18, cursor_y))
                    cursor_y += font.get_linesize() + 2

            cursor_y += 6
            pygame.draw.line(
                screen,
                self.viewer_config.outline_color,
                (panel.x + 18, cursor_y),
                (panel.right - 18, cursor_y),
                width=1,
            )
            cursor_y += 10

    def _handle_keydown(self, key: int) -> None:
        """Handle supported keyboard shortcuts.

        Args:
            key: Pygame key constant. The current implementation reacts to
                ``pygame.K_SPACE`` and ``pygame.K_a``.
        """
        if key == pygame.K_SPACE:
            self._end_turn()
        elif key == pygame.K_a:
            self._toggle_attack_mode()

    def _handle_left_click(self, position: tuple[int, int]) -> None:
        """Handle left-click input for movement or attack targeting.

        Args:
            position: Screen-space click coordinates as integer pixels. Expected
                values are inside the current window bounds.
        """
        tile_coord = self._tile_at_screen_position(position)
        if tile_coord is None:
            self.status_message = "Click a visible tile to select a destination or target."
            return

        self.selected_tile = tile_coord
        if self.interaction_mode == "attack":
            self._handle_attack_click(tile_coord)
            return

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
        """Submit a movement command for the active unit.

        Args:
            target: Destination tile coordinate. It must be inside the map and
                one of the currently reachable tiles for the active unit.
        """
        active_unit_id = self._active_unit().id
        try:
            self.runtime.execute(Command(type="move_unit", unit_id=active_unit_id, target={"x": target.x, "y": target.y}))
        except ValueError as exc:
            self.last_action_message = f"Move failed: {exc}"
            self.status_message = "Pick one of the highlighted tiles to move."
            return

        self.selected_tile = target
        self.last_action_message = f"{active_unit_id} moved to ({target.x}, {target.y})."
        self.status_message = "Move applied. Press A to attack, press Space to end the turn, or click another highlighted tile."

    def _end_turn(self) -> None:
        """Submit an end-turn command for the active unit."""
        active_unit_id = self._active_unit().id
        try:
            self.runtime.execute(Command(type="end_turn", unit_id=active_unit_id))
        except ValueError as exc:
            self.last_action_message = f"End turn failed: {exc}"
            self.status_message = "The active unit cannot end its turn right now."
            return

        new_active_unit = self._active_unit().id
        self.interaction_mode = "move"
        self.selected_tile = self._active_unit().tile_position
        self.last_action_message = f"{active_unit_id} ended its turn. {new_active_unit} is now active."
        self.status_message = "Select a highlighted tile to move the active unit or press A to attack."

    def _toggle_attack_mode(self) -> None:
        """Enter or leave attack-targeting mode for the active unit."""
        if self.interaction_mode == "attack":
            self.interaction_mode = "move"
            self.status_message = "Attack mode canceled. Click a highlighted tile to move the active unit."
            return

        if not self.runtime.current_state().turn.action_available:
            self.status_message = "The active unit has already spent its action."
            return

        attackable_units = self._attackable_units()
        self.interaction_mode = "attack"
        if attackable_units:
            self.status_message = "Attack mode active. Click a highlighted enemy tile to attack."
        else:
            self.status_message = "Attack mode active, but no enemy units are currently in range."

    def _handle_attack_click(self, tile_coord: TileCoord) -> None:
        """Handle a click while attack mode is active.

        Args:
            tile_coord: Clicked tile coordinate. It must match a living hostile
                unit in the legal target set to resolve the action.
        """
        target_unit = self._unit_at_tile(tile_coord)
        if target_unit is None:
            self.status_message = "Click an enemy unit tile to resolve Attack Action."
            return

        attackable_units = self._attackable_units()
        if target_unit.id not in attackable_units:
            self.status_message = "That unit is not a valid attack target for the active unit."
            return

        self._attack_target(target_unit.id)

    def _attack_target(self, target_id: str) -> None:
        """Submit Attack Action against one target unit id.

        Args:
            target_id: Target unit id chosen from the current legal target set.
        """
        active_unit_id = self._active_unit().id
        state = self.runtime.current_state()
        previous_log_length = len(state.log)
        target_tile = state.units[target_id].tile_position
        try:
            self.runtime.execute(Command(type="use_action", unit_id=active_unit_id, action_id="attack", target_id=target_id))
        except ValueError as exc:
            self.last_action_message = f"Attack failed: {exc}"
            self.status_message = "Press A to retry the attack or click a highlighted tile to move."
            return

        new_entries = state.log[previous_log_length:]
        self.selected_tile = target_tile
        self.interaction_mode = "move"
        self.last_action_message = self._resolution_headline()
        if not self.last_action_message:
            self.last_action_message = new_entries[0] if new_entries else f"{active_unit_id} used Attack Action on {target_id}."
        if state.status == "ended":
            self.status_message = "Encounter ended."
        else:
            self.status_message = "Attack resolved. Review LAST ROLL for details, then end the turn or move."

    def _active_unit(self) -> UnitState:
        """Return the unit state for the active turn owner."""
        state = self.runtime.current_state()
        return state.units[state.turn.active_unit_id]

    def _reachable_tiles_for_active_unit(self) -> dict[TileCoord, int]:
        """Return currently reachable tiles for the active unit."""
        state = self.runtime.current_state()
        active_unit = self._active_unit()
        occupied = {unit.tile_position for unit in state.units.values() if unit.alive}
        return reachable_tiles(
            game_map=self.runtime.game_map,
            start=active_unit.tile_position,
            movement_budget=state.turn.remaining_movement,
            occupied=occupied,
        )

    def _attackable_units(self) -> dict[str, UnitState]:
        """Return currently legal attack targets keyed by unit id."""
        target_ids = self.runtime.legal_targets_for_action("attack", unit_id=self._active_unit().id)
        state = self.runtime.current_state()
        return {target_id: state.units[target_id] for target_id in target_ids}

    def _unit_at_tile(self, tile_coord: TileCoord) -> UnitState | None:
        """Return the living unit occupying one tile, if any.

        Args:
            tile_coord: Tile coordinate to inspect. It should lie within the
                loaded map bounds.
        """
        state = self.runtime.current_state()
        for unit in state.units.values():
            if unit.alive and unit.tile_position == tile_coord:
                return unit
        return None

    def _tile_at_screen_position(self, position: tuple[int, int]) -> TileCoord | None:
        """Resolve a screen-space click position to a tile coordinate.

        Args:
            position: Screen-space pixel coordinates. Expected values are inside
                the current window bounds.
        """
        for tile in reversed(sort_tiles_for_render(list(self.runtime.game_map.tiles.values()))):
            if _point_in_polygon(position, tile_polygon(tile, self.projection_config)):
                return tile.coord
        return None

    def _hud_panel_rect(self) -> pygame.Rect:
        """Return the HUD panel rectangle derived from the viewer config."""
        return pygame.Rect(
            self.viewer_config.screen_width - self.viewer_config.hud_width - self.viewer_config.hud_margin,
            self.viewer_config.hud_margin,
            self.viewer_config.hud_width,
            self.viewer_config.screen_height - self.viewer_config.hud_margin * 2,
        )

    def _hud_sections(self) -> list[tuple[str, list[str]]]:
        """Build the grouped HUD sections shown in the viewer."""
        state = self.runtime.current_state()
        selected_tile = self.selected_tile if self.selected_tile is not None else "none"
        return [
            (
                "TURN",
                [
                    f"Encounter {state.encounter_id} | Round {state.turn.round_number}",
                    f"Active: {state.turn.active_unit_id} | Status: {state.status}",
                    f"Move: {state.turn.remaining_movement} | Action: {'Yes' if state.turn.action_available else 'No'}",
                ],
            ),
            (
                "SELECTION",
                [
                    f"Mode: {self.interaction_mode}",
                    f"Tile: {selected_tile}",
                    self.status_message,
                ],
            ),
            (
                "LAST ROLL",
                self._resolution_lines(),
            ),
            (
                "CONTROLS",
                [
                    "Left click: select or move",
                    "A: toggle attack mode",
                    "Space: end turn",
                ],
            ),
        ]

    def _resolution_lines(self) -> list[str]:
        """Build concise viewer lines for the latest structured action result."""
        resolution = self.runtime.current_state().last_resolution
        if resolution is None:
            return [self.last_action_message]

        lines = [
            f"{resolution.actor_id} -> {resolution.target_id} with {resolution.attack_name}",
            f"Roll: d20 {resolution.raw_roll} + {resolution.attack_bonus} = {resolution.total_roll} vs AC {resolution.target_ac}",
            f"Outcome: {self._resolution_outcome_label()}",
        ]
        if resolution.damage is not None:
            damage_values = ", ".join(str(value) for value in resolution.damage.dice_values)
            modifier_sign = "+" if resolution.damage.modifier >= 0 else "-"
            lines.append(
                f"Damage: {resolution.damage.rolled_dice_count}d{resolution.damage.dice_sides}[{damage_values}] "
                f"{modifier_sign} {abs(resolution.damage.modifier)} = {resolution.damage.total}"
            )
        lines.append(f"Target HP: {resolution.target_hp_before} -> {resolution.target_hp_after}")
        return lines

    def _resolution_outcome_label(self) -> str:
        """Return a compact label for the latest structured action result."""
        resolution = self.runtime.current_state().last_resolution
        if resolution is None:
            return "No roll"
        if resolution.critical:
            return "Critical hit"
        if resolution.hit:
            return "Hit"
        if resolution.raw_roll == 1:
            return "Miss (natural 1)"
        return "Miss"

    def _resolution_headline(self) -> str:
        """Return a one-line summary for the latest structured action result."""
        resolution = self.runtime.current_state().last_resolution
        if resolution is None:
            return ""
        if resolution.damage is not None:
            return (
                f"{resolution.attack_name}: d20 {resolution.raw_roll} + {resolution.attack_bonus} = "
                f"{resolution.total_roll} vs AC {resolution.target_ac} -> {self._resolution_outcome_label()} "
                f"for {resolution.damage.total}"
            )
        return (
            f"{resolution.attack_name}: d20 {resolution.raw_roll} + {resolution.attack_bonus} = "
            f"{resolution.total_roll} vs AC {resolution.target_ac} -> {self._resolution_outcome_label()}"
        )


def _tile_color(tile: Tile) -> tuple[int, int, int]:
    """Return the display color for one terrain tile.

    Args:
        tile: Tile to colorize. ``surface_type`` may be any string; blocked
            tiles take precedence over surface type.
    """
    if tile.blocks_movement:
        return (92, 72, 72)
    if tile.surface_type == "ground":
        return (98, 144, 98)
    return (110, 110, 130)


def _unit_color(unit: UnitState, config: ViewerConfig) -> tuple[int, int, int]:
    """Return the display color for one unit marker.

    Args:
        unit: Unit to colorize. The current implementation distinguishes only
            the ``heroes`` team from all others.
        config: Viewer color configuration.
    """
    if unit.team == "heroes":
        return config.hero_unit_color
    return config.enemy_unit_color


def _point_in_polygon(point: tuple[int, int], polygon: list[tuple[int, int]]) -> bool:
    """Check whether a 2D point lies inside a polygon.

    Args:
        point: Screen-space pixel coordinate.
        polygon: Polygon vertices in winding order. The list should contain at
            least three points.
    """
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
    """Wrap one text string into lines that fit a maximum width.

    Args:
        text: Input text. Empty or whitespace-only strings return one empty line.
        font: Font used to measure rendered width.
        max_width: Maximum line width in pixels. Practical values are integers
            ``> 0``.
    """
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
    """Build a projection configuration from the viewer layout.

    Args:
        viewer_config: Viewer layout configuration. Screen width and HUD width
            should leave a positive playable width.
    """
    playable_width = viewer_config.screen_width - viewer_config.hud_width - viewer_config.hud_margin * 3
    origin_x = viewer_config.hud_margin + playable_width // 2
    return ProjectionConfig(origin_x=origin_x, origin_y=180)
