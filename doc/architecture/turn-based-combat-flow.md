# Turn-Based Combat Flow

## Purpose
This document defines the architectural flow for round-based combat so that tactical viewer, headless simulation, and future replay systems all use the same state transitions.

## Core Rule
Combat is processed as a sequence of discrete commands against explicit encounter and turn state. Rendering may happen many times between commands, but combat state only changes when a valid command is applied.

## Encounter States
Suggested high-level states:
- `setup`
- `initiative`
- `turn_start`
- `await_command`
- `resolving_command`
- `turn_end`
- `encounter_end`

The exact implementation can vary, but the architecture should preserve the same lifecycle.

For developers, it is usually enough to implement these as an enum or equivalent state marker on encounter state.

## Round and Turn Lifecycle
1. create encounter from map and participants
2. initialize dynamic encounter state
3. determine initiative order
4. set `round_number = 1`
5. activate the first unit
6. reset per-turn resources
7. accept legal commands for the active unit
8. resolve command side effects
9. keep the turn active until the unit ends its turn or can no longer act
10. advance to the next unit
11. start a new round when initiative order wraps
12. end encounter when victory, defeat, or cancellation condition is met

## Command Boundaries
Version 1 should model at least these commands:
- `start_encounter`
- `move_unit`
- `use_action`
- `attack_target`
- `dash`
- `end_turn`

Commands should:
- reference logical entities and tiles
- be validated before mutation
- produce deterministic state transitions
- be reusable in viewer and headless modes

Example command payloads:

```python
{"type": "use_action", "unit_id": "fighter_1", "action_id": "attack", "target_id": "goblin_2"}
{"type": "attack_target", "unit_id": "fighter_1", "target_id": "goblin_2"}
{"type": "end_turn", "unit_id": "fighter_1"}
```

## Per-Turn Resources
The active turn should track at least:
- remaining movement
- whether the main action is available
- optional reserved fields for bonus action and reaction

This keeps Version 1 simple while staying compatible with DnD-style action economy.

Suggested Version 1 rule interpretation:
- `move_unit` spends movement only
- `use_action` spends the declared action resource according to the action definition
- `attack_target` may remain as a compatibility wrapper over `use_action`
- `dash` spends the main action and increases movement budget according to the simplified DnD rule set
- `end_turn` closes the active unit turn even if resources remain

## Validation Rules
The turn engine should reject commands when:
- the acting unit is not the active unit
- movement exceeds remaining movement
- the action has already been spent
- the target is invalid or out of range
- the combat state is not accepting that command

## Determinism and Replay
For the same encounter definition, seed, and command stream, the combat result should be reproducible.

This is required for:
- automated testing
- headless simulations
- replay support
- debugging of combat bugs

## Viewer Responsibility Boundary
The viewer may:
- display the active unit
- display available actions
- display legal action targets
- send player intent as commands

The viewer must not:
- decide whether a command is legal
- advance initiative
- mutate turn state directly
