from __future__ import annotations

import argparse
from collections.abc import Sequence

from fantasy_strategy_sandbox.app.demo import create_training_yard_runtime
from fantasy_strategy_sandbox.app.runtime import Command


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.mode == "viewer":
        run_viewer(max_frames=args.max_frames)
        return
    run_headless_demo()


def run_headless_demo() -> None:
    runtime = create_training_yard_runtime()
    summary = runtime.summary()
    print(f"Encounter: {summary['encounter_id']}")
    print(f"Map: {summary['map_id']}")
    print(f"Round: {summary['round_number']}")
    print(f"Active unit: {summary['active_unit_id']}")
    print("Units:")
    for unit in summary["units"]:
        print(
            f"  - {unit['id']} ({unit['team']}) at {unit['position']} "
            f"HP {unit['hp']}/{unit['max_hp']}"
        )

    print("\nExample commands:")
    for example in (
        Command(type="move_unit", unit_id=summary["active_unit_id"], target={"x": 2, "y": 1}),
        Command(type="end_turn", unit_id=summary["active_unit_id"]),
    ):
        print(f"  {example}")


def run_viewer(max_frames: int | None = None) -> None:
    from fantasy_strategy_sandbox.render.viewer import TacticalViewer

    runtime = create_training_yard_runtime()
    TacticalViewer(runtime).run(max_frames=max_frames)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fantasy Strategy Sandbox demo launcher.")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("headless", "viewer"),
        default="headless",
        help="Select whether to run the headless demo or the Pygame viewer.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Limit viewer frames for smoke tests or scripted runs.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)
