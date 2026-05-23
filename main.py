from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fantasy_strategy_sandbox.app.runtime import Command, GameRuntime


def main() -> None:
    runtime = GameRuntime.from_files(
        "data/maps/training-yard.json",
        "data/encounters/training-yard-skirmish.json",
    )
    runtime.start_encounter()

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


if __name__ == "__main__":
    main()
