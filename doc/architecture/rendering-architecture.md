# Rendering Architecture

## Goal
Rendering should provide a readable isometric tactical view while staying lightweight and replaceable.

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
- a lightweight Pygame implementation using projected tile diamonds rather than a full 3D engine

Later:
- visible block sides for height steps
- terrain variation through metadata, not custom gameplay logic

## Scene Elements
- terrain
- units
- highlights
- HUD and debug overlays
- future effects

## Current Implementation Status
The current viewer uses:
- **Pygame** as the binding Version 1 rendering stack
- a lightweight isometric-style projection derived from logical tile coordinates
- simple colored terrain polygons
- circular unit markers
- overlay rendering for reachable tiles, selection, and active-turn highlighting
- a grouped HUD panel for turn state, selection context, last-roll breakdown, and controls

This implementation intentionally favors architectural clarity and delivery speed over graphical fidelity.

## Performance Strategy
Version 1 optimizes for modest hardware:
- no complex lighting
- limited color-driven visual language
- lightweight 2D polygon drawing rather than engine-heavy scene management
- small tactical maps

## Invalidation Strategy
Rendering updates should be scoped:
- map changes invalidate terrain presentation
- occupancy changes invalidate unit placement
- query changes invalidate overlays

This keeps the architecture efficient even when future features increase complexity.

## Replaceability
The renderer should be swappable in principle. If the project later changes engine choice, world and combat code should remain largely untouched.
