from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class TileCoord:
    x: int
    y: int


@dataclass(frozen=True)
class Tile:
    coord: TileCoord
    height: int
    surface_type: str
    movement_cost: int
    blocks_movement: bool
    blocks_los: bool
    cover_type: str


@dataclass(frozen=True)
class GameMap:
    map_id: str
    version: int
    width: int
    height: int
    tiles: dict[TileCoord, Tile]
    spawns: dict[str, TileCoord]

    def contains(self, coord: TileCoord) -> bool:
        return coord in self.tiles

    def tile_at(self, coord: TileCoord) -> Tile:
        try:
            return self.tiles[coord]
        except KeyError as exc:
            raise ValueError(f"Unknown tile {coord}.") from exc

    def is_walkable(self, coord: TileCoord, occupied: set[TileCoord] | None = None) -> bool:
        if coord not in self.tiles:
            return False
        tile = self.tiles[coord]
        if tile.blocks_movement:
            return False
        if occupied and coord in occupied:
            return False
        return True
