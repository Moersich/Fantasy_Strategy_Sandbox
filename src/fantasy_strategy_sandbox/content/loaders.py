from __future__ import annotations

import json
from pathlib import Path

from fantasy_strategy_sandbox.combat.models import AttackDefinition, EncounterDefinition, UnitDefinition
from fantasy_strategy_sandbox.world.models import GameMap, Tile, TileCoord


def load_map(path: Path) -> GameMap:
    data = _read_json(path)
    required_keys = {"version", "map_id", "size", "tiles", "spawns"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"Map file is missing keys: {sorted(missing)}")

    width = int(data["size"]["width"])
    height = int(data["size"]["height"])
    tiles: dict[TileCoord, Tile] = {}

    for tile_data in data["tiles"]:
        coord = TileCoord(x=int(tile_data["x"]), y=int(tile_data["y"]))
        if coord in tiles:
            raise ValueError(f"Duplicate tile definition for {coord}.")
        if not (0 <= coord.x < width and 0 <= coord.y < height):
            raise ValueError(f"Tile {coord} is out of bounds.")

        tile = Tile(
            coord=coord,
            height=int(tile_data.get("height", 0)),
            surface_type=str(tile_data.get("surface_type", "ground")),
            movement_cost=int(tile_data.get("movement_cost", 1)),
            blocks_movement=bool(tile_data.get("blocks_movement", False)),
            blocks_los=bool(tile_data.get("blocks_los", False)),
            cover_type=str(tile_data.get("cover_type", "none")),
        )
        tiles[coord] = tile

    spawns: dict[str, TileCoord] = {}
    for spawn_data in data["spawns"]:
        coord = TileCoord(x=int(spawn_data["x"]), y=int(spawn_data["y"]))
        if spawn_data["id"] in spawns:
            raise ValueError(f"Duplicate spawn id {spawn_data['id']}.")
        if coord not in tiles:
            raise ValueError(f"Spawn {spawn_data['id']} references unknown tile {coord}.")
        if tiles[coord].blocks_movement:
            raise ValueError(f"Spawn {spawn_data['id']} references blocked tile {coord}.")
        spawns[str(spawn_data["id"])] = coord

    return GameMap(
        map_id=str(data["map_id"]),
        version=int(data["version"]),
        width=width,
        height=height,
        tiles=tiles,
        spawns=spawns,
    )


def load_encounter(path: Path) -> EncounterDefinition:
    data = _read_json(path)
    required_keys = {"encounter_id", "map_id", "teams"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"Encounter file is missing keys: {sorted(missing)}")

    unit_definitions: list[UnitDefinition] = []
    seen_units: set[str] = set()
    for team_data in data["teams"]:
        team_id = str(team_data["id"])
        for unit_data in team_data["units"]:
            unit_id = str(unit_data["id"])
            if unit_id in seen_units:
                raise ValueError(f"Duplicate unit id {unit_id}.")
            seen_units.add(unit_id)

            attacks = [
                AttackDefinition(
                    name=str(attack["name"]),
                    attack_bonus=int(attack["attack_bonus"]),
                    damage=str(attack["damage"]),
                    range=int(attack.get("range", 1)),
                )
                for attack in unit_data["attacks"]
            ]
            if not attacks:
                raise ValueError(f"Unit {unit_id} must have at least one attack.")

            unit_definitions.append(
                UnitDefinition(
                    id=unit_id,
                    name=str(unit_data["name"]),
                    team=team_id,
                    spawn_id=str(unit_data["spawn_id"]),
                    max_hp=int(unit_data["max_hp"]),
                    hp=int(unit_data.get("hp", unit_data["max_hp"])),
                    ac=int(unit_data["ac"]),
                    speed=int(unit_data["speed"]),
                    initiative_bonus=int(unit_data.get("initiative_bonus", 0)),
                    attacks=attacks,
                )
            )

    return EncounterDefinition(
        encounter_id=str(data["encounter_id"]),
        map_id=str(data["map_id"]),
        initiative_seed=int(data.get("initiative_seed", 0)),
        units=unit_definitions,
    )


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
