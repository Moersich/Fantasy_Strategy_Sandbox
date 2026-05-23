# Runtime Modes

## Goal
The architecture should support multiple runtime modes without changing the gameplay core.

## Mode 1: Tactical Viewer
The tactical viewer is the primary runtime mode for Version 1.

Responsibilities:
- render a small tactical map in a static isometric tactical view
- display units, highlights, and debug overlays
- forward player input to application services
- visualize results returned by the world and combat systems
- present the currently active unit, current round, and available turn actions

Current repository status:
- implemented as a Pygame-based internal demo
- renders the training-yard map
- displays units, active-turn highlighting, reachable tiles, and HUD feedback
- forwards movement and end-turn input into the existing command path

The tactical viewer must not:
- calculate game rules inside render objects
- own authoritative map or unit state
- advance turns on its own outside the combat/turn systems

## Mode 2: Headless Core
The headless core is the currently implemented runtime mode and remains essential for later balancing, automated testing, and AI simulations.

Responsibilities:
- load maps and encounters
- execute turns and rules without rendering
- expose deterministic outputs for tests and statistics
- support automated turn stepping for AI and simulation runs

Current repository status:
- implemented as the current executable slice
- exposed through `main.py` and the `GameRuntime` application service
- covered by automated tests for encounter startup and core commands

Architectural consequence:
- the same world, combat, and query modules must run both with and without graphics
- the same turn engine must process the same command semantics in both modes

## Current Mode Priority
Although the tactical viewer remains the primary product-facing target, the repository currently ships the headless core first. This is intentional architectural sequencing:

1. establish deterministic gameplay state and command handling,
2. validate rules in tests without a renderer,
3. add the viewer as an adapter on top of the same core.

That viewer adapter now exists in a first playable form. The next runtime milestone is therefore a richer viewer increment, not a second gameplay path.

## Future Mode: Map Editing
An editor is a future concern, not a Version 1 requirement.

If added later, the editor should be another adapter on top of the same map format and world model instead of a separate data path.

## Composition Root
The application layer is the composition root. It decides:
- which runtime mode is started
- which renderer is attached
- which input adapter is active
- which content loaders and configuration are used

In a turn-based game it also wires:
- the turn engine
- command handlers for move, attack, dash, and end turn
- presentation state for active-unit and round indicators

## Main Loop
The preferred runtime model is a simple single-process loop:
1. poll input
2. convert input into turn commands
3. validate commands against the current combat state
4. run world/combat/query operations
5. advance or preserve turn state
6. update presentation state
7. render frame

This keeps debugging simple and matches the current project scope.

## Turn Flow Rule
The runtime must be able to pause on a stable combat state between commands. A frame render may happen many times while the same unit remains active, but the combat state only changes when an explicit command is processed.

This is important for:
- deterministic replays
- AI turn execution
- save/load between turns
- debugging of illegal or partial command sequences
