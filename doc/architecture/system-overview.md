# System Overview

## Purpose
This document describes the architecture of the Python-based tactical combat sandbox and its isometric tactical viewer.

The architectural goal is to support:
- lightweight 3D isometric rendering
- small tactical combat maps
- turn-based tactical combat
- strict separation between simulation and rendering
- later extension from flat maps to multi-height block terrain
- later reuse of the same core in headless simulations

## Current Repository State
The repository now contains a working Python headless core and a first playable tactical viewer demo:
- map and encounter content loading from JSON
- combat and turn-state models
- deterministic encounter startup with seeded initiative
- command execution for movement, explicit actions, dash, and end turn
- a first-class Attack Action PoC with simplified DnD-style hit, miss, and crit resolution
- structured combat-resolution data for visible rolls, damage, and HP changes
- movement queries and automated runtime tests
- a Pygame-based viewer runtime
- static isometric-style terrain rendering
- unit visualization, active-turn highlighting, reachable-tile overlays, click-to-move, attack targeting, grouped HUD sections, and end-turn input

The primary architectural gaps are no longer the basic viewer or core integration. The remaining gaps are line-of-sight and cover queries, richer combat interaction, and further demo polish on top of the current viewer slice.

## How To Read This Architecture
For day-to-day implementation work, use the documents in this order:
1. `system-overview.md`
2. `world-and-combat-model.md`
3. `turn-based-combat-flow.md`
4. `runtime-modes.md`
5. `content-and-map-format.md`
6. `implementation-readiness.md`
7. `isometric-projection-and-interaction.md`

This order moves from system boundaries to state model, then to runtime flow, operational mode boundaries, and data contracts.

## Scope of Version 1
Version 1 focuses on:
- static isometric tactical presentation
- flat tactical maps
- simple visuals that run on modest hardware
- explicit round-based play with initiative-driven turns
- DnD combat-relevant map semantics such as movement, occupancy, line of sight, and cover

Version 1 does **not** require:
- free camera rotation
- large explorable worlds
- complex terrain shaders
- fully interactive map editing

## Architectural Principles
1. **Simulation first**: game logic must work without graphics.
2. **World state is authoritative**: rendering mirrors state and never owns gameplay decisions.
3. **Height-ready design**: even flat maps use a model that can later support height.
4. **Deterministic queries**: movement, line of sight, and cover must be testable outside the renderer.
5. **Low-cost visuals**: geometry, lighting, and materials stay simple.
6. **Turn authority lives in the core**: rounds, turns, action usage, and turn transitions are controlled by gameplay services, not by UI timing or render callbacks.

## High-Level Building Blocks
- **Application Layer**: starts the chosen runtime mode and wires the system together.
- **World Core**: owns map tiles, terrain metadata, and occupancy.
- **Combat Core**: applies DnD combat rules to entities and map queries.
- **Turn Engine**: advances initiative order, round progression, and action economy.
- **Spatial Query Layer**: computes movement, range, visibility, and cover.
- **Iso Projection and Interaction Layer**: translates between tile, world, and screen space.
- **Rendering Adapter**: renders terrain, units, highlights, and overlays.
- **Content and Serialization Layer**: loads and validates maps and encounter data.

## Current Package Layout
The current implementation is organized around the following package structure:

```text
project/
  main.py
  src/fantasy_strategy_sandbox/
    app/
      cli.py
      demo.py
      runtime.py
    combat/
      models.py
      turn_engine.py
    content/
      loaders.py
    queries/
      movement.py
    render/
      projection.py
      viewer.py
    world/
      models.py
  tests/
    test_content_loaders.py
    test_demo_runtime.py
    test_render_projection.py
    test_runtime.py
    test_viewer_state_visualization.py
```

This is the current working baseline. The architecture still anticipates additional modules such as `queries/los.py`, `queries/cover.py`, and possibly a dedicated `iso/` package if projection and picking grow beyond the current lightweight adapter implementation.

## Current Delivery Slice
Today the repository delivers two connected runtime slices:

- **Headless Core**
  - load map and encounter data
  - start an encounter deterministically
  - execute discrete turn commands
  - expose available actions and legal targets for the active unit
  - expose structured action-resolution details for logs and CLI output
  - inspect encounter summary in a CLI/demo entry point
  - verify core behavior through automated tests

- **Tactical Viewer Demo**
  - render the training-yard map in a lightweight isometric-style view
  - display units, active turn state, grouped HUD sections, and visible roll feedback
  - show reachable-tile overlays for the active unit
  - forward click-to-move, Attack Action targeting, and end-turn input into the existing core

The next planned delivery slice is not the first viewer itself, but the next viewer increment: richer combat interaction and missing deterministic combat queries such as line of sight and cover.

## Turn-Based Architecture Consequence
The game must behave as a discrete state machine:
- combat starts
- initiative order is established
- one unit becomes active
- only legal commands for that unit are accepted
- action and movement budgets are consumed
- end-turn transitions advance the combat state
- after the last unit acts, a new round begins

This means input is interpreted as **turn commands**, not as free real-time control.

## Dependency Rule
Dependencies must point toward the core:

`Application -> Input / Content / Renderer`

`Application -> World Core / Combat Core / Turn Engine / Spatial Queries`

Adapters communicate with the core through the application layer or stable service interfaces. The reverse direction is not allowed.

## Architecture Documents
- `runtime-modes.md`
- `world-and-combat-model.md`
- `turn-based-combat-flow.md`
- `isometric-projection-and-interaction.md`
- `rendering-architecture.md`
- `content-and-map-format.md`
- `implementation-readiness.md`
