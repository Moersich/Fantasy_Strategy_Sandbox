# Fantasy Strategy Sandbox (D&D 5e Combat Simulator)

## Primary Goals
- Simulate D&D 5e tactical combat accurately enough for experimentation
- Support both manual play and automated AI battles
- Allow thousands of fast simulations for balancing/testing
- Keep the code modular and easy to extend

## Non-Goals (for now)
- Full tabletop rule implementation
- Inventory management
- Complex spell interactions
- Graphics
- Dialogue systems (?)
- Multiplayer (?)

## Core D&D 5e Concepts
### Ability Scores
Every creature has 6 attributes:

### Attribute	Purpose
Strength (STR)	Melee attacks, athletics
Dexterity (DEX)	Initiative, armor, ranged attacks
Constitution (CON)	Hit points, durability
Intelligence (INT)	Knowledge, wizard magic
Wisdom (WIS)	Perception, awareness; cleric, druid and paladin magic
Charisma (CHA)	Leadership, persuasion; warlock and sorcerer magic

### Ability Modifier Formula
The modifier is a core part of a character, as it defines strength and weaknesses

(Ability Score−10)/2

# 3. Dice System

D&D uses dice notation:

*Notation*	*Meaning*
d20	        20-sided die
1d8	        Roll one 8-sided die
2d6	        Roll two 6-sided dice
1d8+3	      Roll 1d8 and add 3

### Important Dice Rules
Advantage:
Roll 2d20 and use the higher result.

Disadvantage:
Roll 2d20 and use the lower result.

# 4. Combat Flow
- Combat Start
- Spawn all units
- Roll initiative:
    Each creature rolls:
    1d20+Initiative Modifier (Highest value acts first)
- Sort units by initiative order

Round Structure

A round represents approximately 6 seconds.

Each unit receives:

- 1 Action
- Movement
- 1 Bonus Action (optional later)
- 1 Reaction (optional later)
Note: It is possible to gain more actions through class feautures or spells. It is common for "Boss"-Monsters to have more turns in a round, since they often act alone.


Turn Sequence:
### Step 1 — Start Turn
- Reset movement
- Reset action flags
- Process begin-of-turn status effects

### Step 2 — Movement
Move across the grid up to movement speed.
Example:
Speed 30 ft = 6 tiles

## Step 3 — Action

### Possible actions:
- Attack
- Dash

for later implementation: 
- Dodge
- Help
- Disengage
- cast a spell
(There are more actions, but I won`t list them all)

### For version 1:
- Attack
- Move
- Dash
are enough.

## Step 4 — End Turn
- Apply end-of-turn effects
- Check deaths
- Advance initiative

## 5. Attack System
Basic Attack Loop:
- Step 1 — Attack Roll
Roll:
1d20 + Attack Bonus

- Step 2 — Hit Check
If:
Attack Roll >= Armor Class
then the attack hits.

### Critical Hits

- A natural 20:
always hits
doubles damage dice or use optional rule "Crunchy Crits": max value of on die + rolled value of the other

Example:

Normal: 1d8+3
Critical: 2d8+3 or with crunchy crits: 8 + 1d8 + 3
Damage

- Subtract damage from HP.

If HP ≤ 0:

monsters die
players become unconscious (optional), unconscious players can be healed to stand again, after 3 failed death saves you die, if you suceed all death saves you stay unconscious

## 6. Armor Class (AC)

Armor Class determines how hard a target is to hit.
Basic Formula
Unarmored AC:
10+DEX Modifier
Armor can override this.

Examples:
Leather Armor: 11 + DEX
Chain Mail: fixed 16
Shield: +2 AC

## 7. Grid & Positioning
Coordinate System

Use:
X coordinate
Y coordinate
Z coordinate for isometric view

Example:
(x, y, z)
Tile Size
1 tile = 5 feet

Distance Calculation

## Original version:
- if grid based:
Diagonal and lateral (horizontal and vertical) movement are treated equal (1 step in each direction correalates to 5 feet)

## Simple version:
Manhattan distance

Advanced version:
- Euclidean distance


### Terrain Types

Possible future terrain:

Floor
Wall
Difficult terrain (see rules)
Water
Lava
Obstacles

## 8. Line of Sight

A unit can only attack if:

target is within range
target is visible

Future system:
ray casting
obstacle blocking

## 9. Data Structures
Unit Structure

Examples of monsters:

goblin = {
    "name": "Goblin",
    "symbol": "G",

    "hp": 7,
    "max_hp": 7,

    "ac": 15,
    "speed": 30,

    "initiative_bonus": 2,

    "attributes": {
        "STR": 8,
        "DEX": 14,
        "CON": 10,
        "INT": 10,
        "WIS": 8,
        "CHA": 8
    },

    "saving_throws": {
        "STR": -1,
        "DEX": 2,
        "CON": 0,
        "INT": 0,
        "WIS": -1,
        "CHA": -1
    },

    "position": [5, 3, 0],

    "attacks": [
        {
            "name": "Scimitar",
            "attack_bonus": 4,
            "damage": "1d6+2",
            "range": 1
        }
    ],

    "alive": True
}

## 10. Engine Systems

The simulator should be divided into systems.

Combat Engine

Handles:

initiative
turns
attacks
damage
death
Movement Engine

Handles:

pathfinding
movement range
collisions

Possible algorithms:

A*
Breadth-first search

AI System handles decision making.

Rendering System

Handles:

ASCII display
terminal updates
animations (optional)

Important:
Rendering should NOT control game logic.

## 11. AI Design
Beginner AI

Simple priorities (possible implementation for stupid characters):

Find nearest enemy
Move toward enemy
Attack if possible
Intermediate AI


Possible heuristics (possible implementation for smart characters):

Focus weakest target
Avoid opportunity attacks
Protect allies
Maintain ranged distance
Advanced AI

Possible future systems:

Utility AI
Behavior trees
Reinforcement learning
Monte Carlo simulations

## 12. Simulation Mode

The engine should support:
Fast Headless Simulation
Run combat without rendering.

Useful for:

balance testing
AI tuning
win-rate statistics

Example:

simulate(10000)

Possible outputs:

average combat duration
win percentage
average remaining HP
damage dealt per unit
13. Status Effects

Future extension system.

Examples:

Poisoned
Stunned
Prone
Burning
Invisible
(there are many more)

Each effect may contain:

{
    "name": "Poisoned",
    "duration": 3,
    "effect": "blah blah blah"
}

## 14. Spell System (Future)

Possible spell categories:

Damage
Healing
Buffs
Debuffs
Area effects

Examples:

Fireball
Magic Missile
Bless
Shield

## 15. ASCII Rendering Example

Example battlefield:

################
#......G.......#
#..............#
#....P.........#
################

Legend:

P = Player
G = Goblin
# = Wall
. = Empty tile

## 16. Suggested Folder Structure
project/
│
├── main.py
├── engine/
│   ├── combat.py
│   ├── movement.py
│   ├── dice.py
│   ├── ai.py
│   └── rendering.py
│
├── data/
│   ├── monsters.json
│   ├── weapons.json
│   └── maps.json
│
├── tests/
│
└── README.md

## 17. Recommended Development Order
- Phase 1
Dice rolling
Unit stats
Turn order
Basic attacks

- Phase 2
Grid movement
Pathfinding
ASCII rendering

- Phase 3
AI movement
Tactical targeting

- Phase 4
Simulation mode
Statistics
Balance testing

- Phase 5
Spells
Status effects
Advanced AI

## 18. Important Simplifications

To avoid project overload:

Recommended Early Simplifications
Ignore spell slots
Ignore reactions
Ignore grappling
Ignore encumbrance
Ignore stealth
Ignore opportunity attacks
Ignore concentration

Implement them later only if needed.

## 19. Long-Term Vision

Possible future features:

Procedural dungeon generation
Campaign simulation
Fog of war
Multiplayer
GUI version
Machine learning AI
Modding support
Replay system
Combat logs
Save/load battles
20. Key Programming Principles
Separate Logic from Rendering

The combat simulation must work even if graphics are disabled.

Deterministic Simulations

Allow fixed random seeds:

random.seed(42)

This makes debugging reproducible.

Keep Systems Modular

Each system should:

have one responsibility
be independently testable
avoid hard dependencies
21. Minimal Viable Product (MVP)

The first playable version only needs:

Grid map
2 teams
Movement
Melee attacks
HP
Initiative
Basic AI
ASCII rendering

Everything else can come later.
