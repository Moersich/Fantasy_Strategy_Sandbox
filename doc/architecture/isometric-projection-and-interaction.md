# Isometric Projection and Interaction

## Goal
This layer defines how logical tiles become visible isometric terrain and how screen interaction maps back to gameplay data.

## Coordinate Spaces

### Tile Space
Logical map coordinates used by world and combat logic.

Example:
- `TileCoord(x, y)`

Height belongs to tile data, not to the coordinate identity. This keeps one logical tile from being mistaken for multiple tiles just because elevation is introduced later.

### World Space
3D scene coordinates used by the renderer.

Responsibilities:
- place terrain blocks
- place units on tile anchors
- define camera-relative geometry

### Screen Space
2D viewport coordinates used for hover, selection, and UI.

## Architectural Rule
Tile space, world space, and screen space must be treated as distinct concepts. Conversion between them belongs in a dedicated projection/interaction layer, not spread across rendering code.

## Camera Strategy
Version 1 uses a static isometric or near-isometric camera:
- fixed angle
- fixed orientation
- optional zoom and pan
- no free rotation required

Preferred properties:
- readable tactical composition
- stable depth perception
- low implementation complexity

## Unit Anchoring
Units should be anchored to the logical center of the tile top surface.

This avoids coupling unit placement to mesh details and keeps the gameplay position deterministic.

## Picking Strategy
Picking should resolve selection in this order:
1. convert pointer position to a world ray or equivalent engine query
2. resolve hit against terrain or unit proxy
3. map the result back to logical tile coordinates
4. pass only logical positions into gameplay services

The gameplay layer must never receive raw engine-specific hit objects as its primary API.

If Version 1 starts without full mouse interaction, the same layer may temporarily expose debug-friendly selection methods such as:
- keyboard cursor movement on tile coordinates
- developer console commands targeting logical tiles
- scripted test inputs for deterministic encounter playback

## Occlusion Policy
Even a static isometric view can hide important information. Version 1 should therefore allow at least one of these mechanisms:
- tile highlight overlays
- clear edge silhouettes
- temporary debug labels

If later height levels are introduced, occlusion handling becomes more important and should remain a renderer concern layered on top of stable world data.
