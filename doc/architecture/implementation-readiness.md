# Implementation Readiness

## Purpose
This document defines what must be clear before implementation of the 3D isometric terrain stack should begin.

## Architecture Is Ready When
- runtime modes are defined
- module boundaries are documented
- world, combat, and query responsibilities are separated
- the project keeps rendering as an adapter instead of the core
- turn ownership and round progression are explicitly modeled in the core
- encounter lifecycle and command boundaries are documented

## Implementation Is Ready When
- Python version and dependency strategy are chosen
- target runtime platform is defined
- a default rendering stack is selected
- the isometric projection and interaction rules are documented
- the map format is documented and versioned
- acceptance criteria for the first prototype exist
- the turn engine contract and command model are documented
- deterministic initiative/replay strategy is decided
- the suggested module split is understood well enough that development can begin without inventing architecture during implementation

## Phase 0 Deliverables
- architecture documents under `doc/architecture/`
- implementation baseline decisions
- projection and picking specification
- JSON map format definition
- turn state and command processing design
- encounter lifecycle specification
- readiness checklist signed off

## Initial Acceptance Criteria

### Phase 1
- project skeleton exists
- runtime mode bootstrapping is clear
- map data can be loaded into the world model
- encounter state can represent round number, active unit, and per-turn resources
- encounter startup can establish a valid initiative order and first active unit

### Phase 2
- a flat tactical map renders in a static isometric view
- units can be placed on tiles
- tile selection or equivalent debug visualization is possible
- the viewer can show whose turn it is without owning turn logic
- presentation can remain stable across multiple frames without changing combat state

### Phase 3
- movement range is computed from logical map data
- occupancy affects movement
- line of sight and cover queries can be tested outside rendering
- move, attack, dash, and end-turn commands are validated against explicit turn state
- end-turn and round-advance transitions are testable without a renderer

## Open Decisions
- whether Version 1 needs interactive map editing
- whether Version 1 needs mouse picking immediately or can start with debug-driven interaction
- whether future elevation expansion should stay block-based only or later add ramps and stairs
- whether initiative should be rolled live each encounter or optionally loaded for deterministic replays

## Developer Review Outcome
At this stage the architecture is complete enough to begin implementation.

The remaining open decisions affect scope and user experience, but they no longer block a first technical slice of:
- map loading
- encounter initialization
- turn sequencing
- flat isometric rendering
- logical movement and attack commands
