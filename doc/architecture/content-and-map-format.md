# Content and Map Format

## Goal
Map content must be editable, serializable, and validatable without relying on renderer internals.

## Version 1 Format
Version 1 should use a simple JSON-based map format.

Reasons:
- easy to inspect
- easy to diff in git
- easy to validate
- sufficient for flat tactical maps

## Required Map Concepts
- map identifier
- format version
- map dimensions
- tile definitions
- blockers
- spawn points
- optional encounter metadata

## Content Separation Rule
Map data and encounter data should be separable.

- **Map data** describes terrain, blockers, and spawn locations.
- **Encounter data** describes participating units, teams, and optional deterministic setup such as initiative seed or predefined initiative order.

This separation keeps the same map reusable across multiple battles.

## Recommended Shape
The exact schema can evolve, but it should clearly separate map metadata from tile data.

Example:

```json
{
  "version": 1,
  "map_id": "training-yard",
  "size": { "width": 12, "height": 12 },
  "tiles": [
    { "x": 0, "y": 0, "height": 0, "surface_type": "ground" }
  ],
  "blockers": [],
  "spawns": [
    { "id": "party_a_1", "x": 1, "y": 1 }
  ]
}
```

Optional encounter example:

```json
{
  "encounter_id": "training-yard-skirmish",
  "map_id": "training-yard",
  "initiative_seed": 42,
  "teams": [
    {
      "id": "heroes",
      "units": [
        { "id": "fighter_1", "spawn_id": "party_a_1" }
      ]
    }
  ]
}
```

## Validation Rules
The content layer should validate:
- coordinates are inside bounds
- tile definitions are not duplicated
- spawn points refer to valid, walkable tiles
- required fields exist
- version is supported

If encounter data is present, validation should also ensure:
- unit spawn references are valid
- teams are defined consistently
- initiative inputs are structurally valid

## Future-Proofing
Even flat maps should reserve room for later features:
- `height`
- cover metadata
- terrain cost
- special traversal markers such as ramps or stairs
- encounter setup metadata for deterministic replays or test fixtures

## Architectural Rule
Content files describe intent and state. They must not embed renderer-specific mesh instructions as the primary source of truth.

## Developer Guidance
For implementation clarity:
- keep map files reusable across many encounters
- keep encounter files small and battle-specific
- validate content before runtime systems create world or combat state
