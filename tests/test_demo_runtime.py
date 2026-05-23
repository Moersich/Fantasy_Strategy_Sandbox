import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.app.demo import create_training_yard_runtime


class DemoRuntimeTests(unittest.TestCase):
    def test_create_training_yard_runtime_starts_encounter_by_default(self) -> None:
        """Verify the demo runtime auto-starts combat by default."""
        runtime = create_training_yard_runtime()

        self.assertEqual(runtime.game_map.map_id, "training-yard")
        self.assertEqual(runtime.current_state().encounter_id, "training-yard-skirmish")

    def test_create_training_yard_runtime_can_skip_startup(self) -> None:
        """Verify demo runtime creation can skip encounter startup."""
        runtime = create_training_yard_runtime(start_encounter=False)

        self.assertIsNone(runtime.encounter_state)


if __name__ == "__main__":
    unittest.main()
