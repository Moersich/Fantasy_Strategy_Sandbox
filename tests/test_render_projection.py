import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.render.projection import ProjectionConfig, project_tile, sort_tiles_for_render, tile_polygon
from fantasy_strategy_sandbox.world.models import Tile, TileCoord


class RenderProjectionTests(unittest.TestCase):
    def test_project_tile_returns_stable_center_point(self) -> None:
        config = ProjectionConfig(tile_width=96, tile_height=48, origin_x=300, origin_y=120)

        self.assertEqual(project_tile(TileCoord(2, 1), 0, config), (348, 192))

    def test_tile_polygon_creates_diamond_points(self) -> None:
        tile = Tile(
            coord=TileCoord(1, 1),
            height=0,
            surface_type="ground",
            movement_cost=1,
            blocks_movement=False,
            blocks_los=False,
            cover_type="none",
        )
        config = ProjectionConfig(tile_width=80, tile_height=40, origin_x=200, origin_y=100)

        self.assertEqual(
            tile_polygon(tile, config),
            [(200, 120), (240, 140), (200, 160), (160, 140)],
        )

    def test_sort_tiles_for_render_orders_by_painting_depth(self) -> None:
        tiles = [
            Tile(TileCoord(2, 0), 0, "ground", 1, False, False, "none"),
            Tile(TileCoord(0, 0), 0, "ground", 1, False, False, "none"),
            Tile(TileCoord(1, 0), 0, "ground", 1, False, False, "none"),
        ]

        ordered = sort_tiles_for_render(tiles)

        self.assertEqual([tile.coord for tile in ordered], [TileCoord(0, 0), TileCoord(1, 0), TileCoord(2, 0)])


if __name__ == "__main__":
    unittest.main()
