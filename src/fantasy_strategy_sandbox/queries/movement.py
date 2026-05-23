from __future__ import annotations

from collections import deque

from fantasy_strategy_sandbox.world.models import GameMap, TileCoord


_DIRECTIONS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


def reachable_tiles(
    game_map: GameMap,
    start: TileCoord,
    movement_budget: int,
    occupied: set[TileCoord],
) -> dict[TileCoord, int]:
    """Compute reachable tiles and their total movement cost.

    Args:
        game_map: Map used for tile existence, walkability, and movement cost
            lookups.
        start: Origin tile for the search. It should exist on ``game_map``.
        movement_budget: Maximum total movement cost the unit may spend.
            Expected range is ``>= 0``.
        occupied: Tiles currently occupied by living units. Any tile in this set
            blocks movement except the ``start`` tile.
    """
    visited: dict[TileCoord, int] = {start: 0}
    queue: deque[TileCoord] = deque([start])

    while queue:
        current = queue.popleft()
        current_cost = visited[current]

        for neighbor in neighbors(current):
            if not game_map.contains(neighbor):
                continue

            occupied_blockers = occupied - {start}
            if not game_map.is_walkable(neighbor, occupied_blockers):
                continue

            step_cost = game_map.tile_at(neighbor).movement_cost
            new_cost = current_cost + step_cost
            if new_cost > movement_budget:
                continue

            if neighbor not in visited or new_cost < visited[neighbor]:
                visited[neighbor] = new_cost
                queue.append(neighbor)

    return visited


def grid_distance(start: TileCoord, end: TileCoord) -> int:
    """Return Chebyshev grid distance for 8-direction movement.

    Args:
        start: Origin tile coordinate.
        end: Destination tile coordinate.
    """
    return max(abs(start.x - end.x), abs(start.y - end.y))


def neighbors(coord: TileCoord) -> list[TileCoord]:
    """Return the 8 neighboring tile coordinates around one tile.

    Args:
        coord: Center tile coordinate.
    """
    return [TileCoord(coord.x + dx, coord.y + dy) for dx, dy in _DIRECTIONS]
