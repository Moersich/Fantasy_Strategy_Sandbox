# Fantasy Strategy Sandbox

Fantasy Strategy Sandbox is a Python-based tactical combat sandbox focused on a deterministic, turn-based core that can later drive both a headless simulation mode and a tactical viewer.

## Current implementation status

The repository already contains a working headless core slice for a small flat combat map:

- JSON-based map loading
- JSON-based encounter loading
- deterministic encounter startup with seeded initiative
- turn handling for `move_unit`, `attack_target`, `dash`, and `end_turn`
- movement reachability queries
- automated tests for the current runtime behavior

The tactical viewer described in the architecture documents is **not** implemented yet. The current executable slice is the headless runtime.

## Running the current runtime slice

Run the demo encounter from the project root:

```bash
python3 main.py
```

This starts the headless runtime, loads the training-yard encounter, and prints a summary of the current combat state plus example commands.

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
