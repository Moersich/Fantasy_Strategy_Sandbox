import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fantasy_strategy_sandbox.app.demo import create_training_yard_runtime
from fantasy_strategy_sandbox.app.cli import run_headless_demo


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

    def test_run_headless_demo_prints_structured_roll_resolution(self) -> None:
        """Verify the headless demo prints visible roll and damage details."""
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            run_headless_demo()

        rendered = output.getvalue()
        self.assertIn("After scripted sample:", rendered)
        self.assertIn("Last resolution:", rendered)
        self.assertIn("Roll: d20 19 + 4 = 23 vs AC 16", rendered)
        self.assertIn("Damage: 1d6[", rendered)


if __name__ == "__main__":
    unittest.main()
