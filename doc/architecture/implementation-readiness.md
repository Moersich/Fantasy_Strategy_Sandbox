# Implementation Readiness

## Purpose
This document defines which architectural prerequisites are already satisfied, which implementation slices are complete, and what still must be decided before the tactical viewer is built.

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

## Current Repository Baseline

The following pieces already exist in code:

- Python project skeleton and package layout
- headless runtime bootstrapping via `main.py`
- JSON map loading
- JSON encounter loading
- encounter state and turn state models
- deterministic initiative and encounter startup
- command execution for movement, attack, dash, and end turn
- movement-range query logic
- automated runtime tests

## Already Completed Foundation Deliverables
- architecture documents under `doc/architecture/`
- Python baseline decisions in `pyproject.toml`
- JSON map format definition
- turn state and command processing design
- encounter lifecycle specification
- first executable headless combat slice

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

### Phase 3 - Tactical viewer vertical slice
- a flat tactical map renders in a static isometric view
- units can be placed on tiles
- tile selection or equivalent debug visualization is possible
- the viewer can show whose turn it is without owning turn logic
- presentation can remain stable across multiple frames without changing combat state

### Phase 4 - Query completion for combat presentation
- movement range is computed from logical map data
- occupancy affects movement
- line of sight and cover queries can be tested outside rendering
- move, attack, dash, and end-turn commands are validated against explicit turn state
- end-turn and round-advance transitions are testable without a renderer

**Status:** partially complete. Movement and turn validation exist; line of sight and cover are still missing.

## Open Decisions
- whether Version 1 needs interactive map editing
- whether Version 1 needs mouse picking immediately or can start with debug-driven interaction
- whether future elevation expansion should stay block-based only or later add ramps and stairs
- whether initiative should be rolled live each encounter or optionally loaded for deterministic replays
- which rendering stack is the binding Version 1 choice for the tactical viewer

## Current Recommended Next Step
The next implementation step should not be rendering yet. It should be:

1. synchronize project-level documentation with the actual headless core,
2. harden the headless core with negative tests and clearer validation,
3. complete missing deterministic combat queries,
4. then begin the tactical viewer against the stabilized core.

## Developer Review Outcome
At this stage the architecture is complete enough to continue implementation from an existing core rather than from a blank slate.

The remaining open decisions affect scope and user experience, but they no longer block the current technical slice of:
- map loading
- encounter initialization
- turn sequencing
- logical movement and attack commands

They do still affect the next viewer-oriented slice.
