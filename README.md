# Fantasy Strategy Sandbox

Fantasy Strategy Sandbox is a Python-based tactical combat sandbox with a deterministic, turn-based core that now drives both a headless simulation mode and a tactical viewer demo.

## Current implementation status

The repository currently contains:

- JSON-based map loading
- JSON-based encounter loading
- deterministic encounter startup with seeded initiative
- turn handling for `move_unit`, `use_action`, `attack_target`, `dash`, and `end_turn`
- a first-class Attack Action PoC with simplified DnD 5e hit, miss, and crit handling
- structured attack resolution output with visible d20 rolls, AC comparison, and damage breakdowns
- movement reachability queries
- a Pygame-based tactical viewer foundation with static isometric map rendering
- a playable viewer demo with movement, turn ending, overlays, structured HUD sections, and on-screen feedback
- automated tests for the current runtime behavior

The current viewer implementation now supports map rendering, unit visualization, active-turn display, movement selection, Attack Action targeting, end-turn input, grouped HUD sections, and visible roll feedback.

## Starting the project

Install the project and its dependencies from the project root:

```bash
python3 -m pip install -e .
```

### Headless demo

Run the headless demo encounter:

```bash
python3 main.py headless
```

If no mode is provided, `headless` is used by default.

This starts the headless runtime, loads the training-yard encounter, prints the current combat state, then runs a deterministic sample sequence and shows the full attack resolution including d20 roll, AC comparison, damage dice, and HP change.

### Tactical viewer

Run the Pygame viewer:

```bash
python3 main.py viewer
```

This starts the current interactive rendering demo for the training-yard map.

Viewer controls:

- left click on a highlighted tile to move the active unit
- press `A` to toggle Attack Action targeting for the active unit
- left click on a highlighted enemy tile in attack mode to use Attack Action
- left click on any other tile to inspect or attempt a destination/target
- press `Space` to end the current unit's turn

For a short smoke test run, you can limit the viewer loop:

```bash
python3 main.py viewer --max-frames 1
```

## Architecture documentation

The main architecture documents live under `doc/architecture/`.

Recommended reading order:

1. `doc/architecture/system-overview.md`
2. `doc/architecture/world-and-combat-model.md`
3. `doc/architecture/turn-based-combat-flow.md`
4. `doc/architecture/runtime-modes.md`
5. `doc/architecture/content-and-map-format.md`
6. `doc/architecture/implementation-readiness.md`

## Running tests

Run all existing test cases from the project root with `unittest`:

```bash
python3 -m unittest discover -s tests -v
```

## PyCharm run configuration

A matching PyCharm run configuration is available at `.idea/runConfigurations/All_tests.xml`.

It runs the same test suite for the entire `tests` directory with the project root as the working directory.
