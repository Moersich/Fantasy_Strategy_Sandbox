# Implementation Readiness

## Purpose
This document defines which architectural prerequisites are already satisfied, which implementation slices are complete, and what remains after the first playable tactical viewer demo.

## Architecture Is Ready When
- runtime modes are defined
- module boundaries are documented
- world, combat, and query responsibilities are separated
- the project keeps rendering as an adapter instead of the core
- turn ownership and round progression are explicitly modeled in the core
- encounter lifecycle and command boundaries are documented

**Current assessment:** these conditions are already met well enough for continued implementation.

## Viewer Implementation Is Ready When
- Python version and dependency strategy are chosen
- target runtime platform is defined
- a default rendering stack is selected
- the isometric projection and interaction rules are documented
- the map format is documented and versioned
- acceptance criteria for the first prototype exist
- the turn engine contract and command model are documented
- deterministic initiative/replay strategy is decided
- the current headless core is robust enough to serve as the single gameplay authority

**Current assessment:** these conditions are met for the current Pygame-based viewer demo.

## Current Repository Baseline

The following pieces already exist in code:

- Python project skeleton and package layout
- headless runtime bootstrapping via `main.py`
- JSON map loading
- JSON encounter loading
- encounter state and turn state models
- deterministic initiative and encounter startup
- command execution for movement, Attack Action, dash, and end turn
- an explicit action-selection/query surface for the active unit
- movement-range query logic
- Pygame viewer entry and runtime split
- isometric-style map rendering
- unit rendering, active-turn highlighting, reachable-tile overlays, and HUD feedback
- viewer input for movement and end turn
- automated runtime tests

## Already Completed Foundation Deliverables
- architecture documents under `doc/architecture/`
- Python baseline decisions in `pyproject.toml`
- JSON map format definition
- turn state and command processing design
- encounter lifecycle specification
- first executable headless combat slice
- first playable tactical viewer demo

## Delivery Acceptance Criteria

### Phase 1 - Headless core baseline
- project skeleton exists
- runtime mode bootstrapping is clear
- map data can be loaded into the world model
- encounter state can represent round number, active unit, and per-turn resources
- encounter startup can establish a valid initiative order and first active unit

**Status:** complete

### Phase 2 - Headless core hardening
- negative tests exist for illegal commands and invalid content
- turn transitions across round boundaries are explicitly covered
- encounter end conditions are covered by tests
- runtime/demo entry point is documented and stable

**Status:** complete

### Phase 3 - Tactical viewer vertical slice
- a flat tactical map renders in a static isometric view
- units can be placed on tiles
- tile selection or equivalent debug visualization is possible
- the viewer can show whose turn it is without owning turn logic
- presentation can remain stable across multiple frames without changing combat state

**Status:** complete

### Phase 4 - Query completion for combat presentation
- movement range is computed from logical map data
- occupancy affects movement
- line of sight and cover queries can be tested outside rendering
- move, attack, dash, and end-turn commands are validated against explicit turn state
- available actions and legal targets can be queried without renderer-owned rules
- end-turn and round-advance transitions are testable without a renderer

**Status:** mostly complete for the current slice. Movement, turn validation, Attack Action flow, and action-target queries exist; line of sight and cover are still missing.

## Open Decisions
- whether Version 1 needs interactive map editing
- whether Version 1 should keep the current simple click interaction or evolve to more precise tile picking
- whether future elevation expansion should stay block-based only or later add ramps and stairs
- whether initiative should be rolled live each encounter or optionally loaded for deterministic replays

## Binding Decisions
- Version 1 uses **Pygame** as the rendering stack for the tactical viewer.

## Current Recommended Next Step
The next implementation step should build on the playable viewer demo:

1. complete missing deterministic combat queries such as line of sight and cover,
2. expand viewer interaction beyond movement, Attack Action, and end turn,
3. add richer combat feedback and scenario coverage,
4. keep the viewer aligned with the same core command model.

## Developer Review Outcome
At this stage the architecture is complete enough to continue implementation from an existing core rather than from a blank slate.

The remaining open decisions affect scope and user experience, but they no longer block the current technical slices of:
- map loading
- encounter initialization
- turn sequencing
- logical movement and attack commands
- first-playable viewer delivery

They do still affect the next combat and presentation increments.
