# System Overview

## Purpose
This document describes the target architecture for the Python-based 3D isometric terrain layer of the DnD strategy sandbox.

The architectural goal is to support:
- lightweight 3D isometric rendering
- small tactical combat maps
- turn-based tactical combat
- strict separation between simulation and rendering
- later extension from flat maps to multi-height block terrain
- later reuse of the same core in headless simulations

## Current Repository State
The repository currently contains project notes and DnD rule summaries, but no Python implementation yet. This architecture therefore defines the target structure before code is written.

## How To Read This Architecture
For day-to-day implementation work, use the documents in this order:
1. `system-overview.md`
2. `world-and-combat-model.md`
3. `turn-based-combat-flow.md`
4. `isometric-projection-and-interaction.md`
5. `content-and-map-format.md`
6. `implementation-readiness.md`

This order moves from system boundaries to state model, then to runtime flow and data contracts.

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

## Suggested Package Layout
The exact implementation can evolve, but the current architecture maps naturally to a structure like:

```text
project/
  main.py
  app/
    runtime.py
    command_dispatch.py
  world/
    map_state.py
    occupancy.py
  combat/
    encounter_state.py
    rules.py
    turn_engine.py
  queries/
    movement.py
    los.py
    cover.py
  render/
    scene_builder.py
    overlays.py
    camera.py
  iso/
    projection.py
    picking.py
  content/
    map_loader.py
    encounter_loader.py
    validation.py
```

This is not a fixed contract, but it gives developers a concrete starting translation from architecture to code.

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

## Planned Architecture Documents
- `runtime-modes.md`
- `world-and-combat-model.md`
- `turn-based-combat-flow.md`
- `isometric-projection-and-interaction.md`
- `rendering-architecture.md`
- `content-and-map-format.md`
- `implementation-readiness.md`
