# Rendering Architecture

## Goal
Rendering should provide a readable 3D isometric tactical view while staying lightweight and replaceable.

## Renderer Role
The renderer is an adapter. It consumes world and query state and produces visuals.

It must not:
- decide movement legality
- own combat flow
- compute authoritative line of sight

## Terrain Generation Strategy
Terrain geometry should be generated from map data instead of stored as handcrafted scene data.

Version 1:
- flat terrain tiles
- simple top surfaces
- low visual complexity

Later:
- visible block sides for height steps
- terrain variation through metadata, not custom gameplay logic

## Scene Elements
- terrain
- units
- highlights
- debug overlays
- future effects

## Performance Strategy
Version 1 optimizes for modest hardware:
- simple lighting
- limited material variety
- reused tile meshes or instancing where supported
- small tactical maps

## Invalidation Strategy
Rendering updates should be scoped:
- map changes invalidate terrain presentation
- occupancy changes invalidate unit placement
- query changes invalidate overlays

This keeps the architecture efficient even when future features increase complexity.

## Replaceability
The renderer should be swappable in principle. If the project later changes engine choice, world and combat code should remain largely untouched.
