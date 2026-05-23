# System Overview

## Purpose
This document describes the target architecture for the Python-based tactical combat sandbox and its later 3D isometric viewer.

The architectural goal is to support:
- lightweight 3D isometric rendering
- small tactical combat maps
- turn-based tactical combat
- strict separation between simulation and rendering
- later extension from flat maps to multi-height block terrain
- later reuse of the same core in headless simulations

## Current Repository State
The repository already contains a working Python headless core slice:
- map and encounter content loading from JSON
- combat and turn-state models
- deterministic encounter startup with seeded initiative
- command execution for movement, attack, dash, and end turn
- movement queries and automated runtime tests

The primary architectural gap is no longer the gameplay core, but the absence of the tactical viewer, line-of-sight/cover queries, and a synchronized project-level roadmap in the documentation.

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
- static 3D isometric camera
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
      runtime.py
    combat/
      models.py
      turn_engine.py
    content/
      loaders.py
    queries/
      movement.py
    world/
      models.py
  tests/
    test_runtime.py
```

This is the current working baseline. The architecture still anticipates additional packages such as `render/`, `iso/`, and more query modules like `los.py` and `cover.py`, but those are future implementation targets rather than current repository contents.

## Current Delivery Slice
Today the repository delivers the **Headless Core** runtime mode:
- load map and encounter data
- start an encounter deterministically
- execute discrete turn commands
- inspect encounter summary in a CLI/demo entry point
- verify core behavior through automated tests

The next planned delivery slice is the **Tactical Viewer**, which should remain an adapter over the same core instead of becoming a second gameplay implementation.

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
