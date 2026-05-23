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
        """Check whether a tile coordinate exists on the loaded map.

        Args:
            coord: Tile coordinate to test. Valid x/y ranges are
                ``0 <= x < width`` and ``0 <= y < height``.
        """
        return coord in self.tiles

    def tile_at(self, coord: TileCoord) -> Tile:
        """Return the tile at one coordinate or raise on unknown tiles.

        Args:
            coord: Tile coordinate to read. Valid x/y ranges are
                ``0 <= x < width`` and ``0 <= y < height``.
        """
        try:
            return self.tiles[coord]
        except KeyError as exc:
            raise ValueError(f"Unknown tile {coord}.") from exc

    def is_walkable(self, coord: TileCoord, occupied: set[TileCoord] | None = None) -> bool:
        """Check whether a tile can be entered by movement.

        Args:
            coord: Tile coordinate to validate. Coordinates outside the map are
                rejected immediately.
            occupied: Optional set of blocked tile coordinates. ``None`` means
                only terrain blockers apply.
        """
        if coord not in self.tiles:
            return False
        tile = self.tiles[coord]
        if tile.blocks_movement:
            return False
        if occupied and coord in occupied:
            return False
        return True
