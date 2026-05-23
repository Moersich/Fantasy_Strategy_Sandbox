# World and Combat Model

## Design Goal
The world model must support DnD tactical combat while staying independent of rendering technology.

## State Categories

### 1. Static Map State
Static map state exists before a battle starts.

Examples:
- map dimensions
- tile coordinates
- terrain type
- blockers
- cover markers
- spawn points
- future height values

### 2. Dynamic Encounter State
Dynamic encounter state changes during combat.

Examples:
- unit positions
- initiative order
- current round number
- active unit id
- turn phase
- remaining movement
- action availability
- hit points
- active effects
- turn state

### 3. Derived Query State
Derived query state is computed on demand and should not be persisted as the source of truth.

Examples:
- reachable tiles
- visible targets
- range overlays
- cover results

## Core Data Model

## Terminology
- **TileCoord**: logical 2D grid position, usually `x` and `y`
- **Tile height**: terrain property stored on the tile, not part of the coordinate identity
- **World position**: 3D render-space location derived from tile data
- **Encounter state**: all mutable combat data for one battle
- **Turn state**: the currently active round/turn/action-economy subset of encounter state

Using these terms consistently avoids a common implementation mistake: treating terrain height as if it were part of the logical tile identity.

### Tile
A tile should be modeled as logical terrain data, not as a render node.

Suggested properties:
- `x`
- `y`
- `height`
- `surface_type`
- `movement_cost`
- `blocks_movement`
- `blocks_los`
- `cover_type`

### Unit
A unit belongs to encounter state and references tiles by logical position.

Suggested properties:
- `id`
- `name`
- `tile_position`
- `team`
- `hp`
- `ac`
- `speed`
- `attacks`
- `status_effects`

### Turn State
Turn state must be explicit and serializable instead of being inferred from UI state.

Suggested properties:
- `round_number`
- `initiative_order`
- `initiative_seed` or equivalent replay input
- `active_unit_id`
- `turn_phase`
- `remaining_movement`
- `action_available`
- `bonus_action_available`
- `reaction_available`

Version 1 may defer bonus actions and reactions in rules execution, but the architecture should reserve space for them because they are part of DnD combat structure.

## Module Responsibilities

### World Core
- owns map tiles
- manages occupancy
- exposes terrain queries

### Combat Core
- owns turn flow and DnD rule execution
- reads world and query results
- never depends on renderer state

### Turn Engine
- starts encounters
- rolls or assigns initiative
- selects the active unit
- tracks round progression
- resets per-turn resources
- closes turns and advances initiative
- rejects commands that do not match the active unit or current turn phase

### Spatial Query Layer
- provides adjacency
- provides movement reachability
- provides line of sight
- provides cover and range lookups

## Command Model
The combat architecture should accept discrete commands such as:
- `start_encounter`
- `move_unit`
- `use_action`
- `attack_target`
- `dash`
- `end_turn`

Each command is validated against explicit turn state before it mutates encounter data.

This is important because:
- the tactical viewer can submit commands one by one
- the headless core can replay the same command stream deterministically
- illegal actions can be rejected without mixing UI and combat rules

Suggested command shape:

```python
{
    "type": "move_unit",
    "unit_id": "fighter_1",
    "target": {"x": 4, "y": 6}
}
```

The important part is not the exact syntax but the boundary: commands reference logical IDs and logical tile coordinates, never renderer objects.

For Version 1, `attack_target` may exist as a compatibility wrapper, but the preferred long-term pattern is a generic `use_action` command plus action metadata and legal-target queries owned by the combat core.

## Encounter Lifecycle
The encounter lifecycle should be modeled as a stable sequence:
1. load map and encounter participants
2. initialize encounter state
3. determine initiative order
4. open first turn
5. accept validated commands for the active unit
6. close turn and advance order
7. open next round when the order wraps
8. end encounter when a victory, defeat, or abort condition is met

## Turn-Based Rule
At any point in combat, exactly one unit is active or combat is outside an active turn boundary. Only the active unit can spend movement or actions until the turn engine advances state.

## Determinism Rule
Initiative ordering, command validation, and turn advancement must be deterministic for the same seed and command stream. This is required for headless simulation, replay, and debugging.

## Architectural Rule
The world model must remain usable in a headless test without any rendering engine attached.

## Version 1 Constraint
Version 1 maps are flat, but the model must keep `height` in the schema from day one so later terrain expansion does not require a redesign.

## Version 1 Gameplay Simplifications
To keep the first implementation understandable and shippable:
- support `move`, `attack`, `dash`, and `end_turn`
- expose legal Attack Action targets through the core so the viewer does not own attack validation
- reserve fields for bonus action and reaction, but allow their rule handling to come later
- allow line-of-sight and cover to start simple as long as they stay outside the renderer
