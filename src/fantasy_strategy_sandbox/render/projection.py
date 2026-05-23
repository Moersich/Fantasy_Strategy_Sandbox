from __future__ import annotations

from dataclasses import dataclass

from fantasy_strategy_sandbox.world.models import Tile, TileCoord


@dataclass(frozen=True)
class ProjectionConfig:
    tile_width: int = 96
    tile_height: int = 48
    elevation_height: int = 12
    origin_x: int = 480
    origin_y: int = 140


def project_tile(coord: TileCoord, height: int, config: ProjectionConfig) -> tuple[int, int]:
    """Project one logical tile coordinate into screen space.

    Args:
        coord: Logical tile coordinate on the tactical grid.
        height: Tile elevation in map units. Expected range is ``>= 0`` for the
            current flat-map slice.
        config: Projection constants. ``tile_width`` and ``tile_height`` should
            be positive integers.
    """
    half_width = config.tile_width // 2
    half_height = config.tile_height // 2
    center_x = (coord.x - coord.y) * half_width + config.origin_x
    center_y = (coord.x + coord.y) * half_height + config.origin_y - height * config.elevation_height
    return center_x, center_y


def tile_polygon(tile: Tile, config: ProjectionConfig) -> list[tuple[int, int]]:
    """Return the four diamond vertices used to render one tile.

    Args:
        tile: Tile to project. Its coordinate must belong to the rendered map.
        config: Projection constants with positive tile dimensions.
    """
    center_x, center_y = project_tile(tile.coord, tile.height, config)
    half_width = config.tile_width // 2
    half_height = config.tile_height // 2
    return [
        (center_x, center_y - half_height),
        (center_x + half_width, center_y),
        (center_x, center_y + half_height),
        (center_x - half_width, center_y),
    ]


def unit_anchor(coord: TileCoord, height: int, config: ProjectionConfig) -> tuple[int, int]:
    """Return the screen anchor used to draw a unit marker on a tile.

    Args:
        coord: Logical tile coordinate where the unit stands.
        height: Tile elevation in map units. Expected range is ``>= 0`` for the
            current flat-map slice.
        config: Projection constants with positive tile dimensions.
    """
    center_x, center_y = project_tile(coord, height, config)
    return center_x, center_y - config.tile_height // 6


def sort_tiles_for_render(tiles: list[Tile]) -> list[Tile]:
    """Sort tiles by painter's-order depth for isometric rendering.

    Args:
        tiles: Tiles to sort. The list may be empty.
    """
    return sorted(tiles, key=lambda tile: (tile.coord.x + tile.coord.y, tile.coord.x, tile.coord.y))
