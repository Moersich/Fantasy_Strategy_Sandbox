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
    half_width = config.tile_width // 2
    half_height = config.tile_height // 2
    center_x = (coord.x - coord.y) * half_width + config.origin_x
    center_y = (coord.x + coord.y) * half_height + config.origin_y - height * config.elevation_height
    return center_x, center_y


def tile_polygon(tile: Tile, config: ProjectionConfig) -> list[tuple[int, int]]:
    center_x, center_y = project_tile(tile.coord, tile.height, config)
    half_width = config.tile_width // 2
    half_height = config.tile_height // 2
    return [
        (center_x, center_y - half_height),
        (center_x + half_width, center_y),
        (center_x, center_y + half_height),
        (center_x - half_width, center_y),
    ]


def sort_tiles_for_render(tiles: list[Tile]) -> list[Tile]:
    return sorted(tiles, key=lambda tile: (tile.coord.x + tile.coord.y, tile.coord.x, tile.coord.y))
