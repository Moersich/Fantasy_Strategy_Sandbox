import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.content.loaders import load_encounter, load_map


class ContentLoaderTests(unittest.TestCase):
    def test_load_map_rejects_unsupported_version(self) -> None:
        """Verify map loading rejects unsupported version numbers."""
        map_data = {
            "version": 2,
            "map_id": "invalid-map",
            "size": {"width": 1, "height": 1},
            "tiles": [{"x": 0, "y": 0}],
            "spawns": [],
        }

        path = self._write_json(map_data)

        with self.assertRaisesRegex(ValueError, "Unsupported map version 2"):
            load_map(path)

    def test_load_map_rejects_non_positive_movement_cost(self) -> None:
        """Verify map loading rejects zero or negative movement cost."""
        map_data = {
            "version": 1,
            "map_id": "invalid-map",
            "size": {"width": 1, "height": 1},
            "tiles": [{"x": 0, "y": 0, "movement_cost": 0}],
            "spawns": [],
        }

        path = self._write_json(map_data)

        with self.assertRaisesRegex(ValueError, "positive movement cost"):
            load_map(path)

    def test_load_encounter_rejects_empty_teams(self) -> None:
        """Verify encounter loading rejects missing teams."""
        encounter_data = {
            "encounter_id": "invalid-encounter",
            "map_id": "training-yard",
            "teams": [],
        }

        path = self._write_json(encounter_data)

        with self.assertRaisesRegex(ValueError, "Encounter must define at least one team"):
            load_encounter(path)

    def test_load_encounter_rejects_hp_outside_valid_range(self) -> None:
        """Verify encounter loading rejects HP outside ``0..max_hp``."""
        encounter_data = {
            "encounter_id": "invalid-encounter",
            "map_id": "training-yard",
            "teams": [
                {
                    "id": "heroes",
                    "units": [
                        {
                            "id": "fighter_1",
                            "name": "Fighter",
                            "spawn_id": "heroes-a",
                            "max_hp": 10,
                            "hp": 11,
                            "ac": 16,
                            "speed": 6,
                            "attacks": [{"name": "Sword", "attack_bonus": 5, "damage": "1d8+3", "range": 1}],
                        }
                    ],
                }
            ],
        }

        path = self._write_json(encounter_data)

        with self.assertRaisesRegex(ValueError, "hp outside the valid range"):
            load_encounter(path)

    def _write_json(self, payload: dict) -> Path:
        """Write one JSON fixture file for loader tests.

        Args:
            payload: JSON-serializable object. The current tests pass mapping
                payloads that match the expected file schema.
        """
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "fixture.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return path


if __name__ == "__main__":
    unittest.main()
