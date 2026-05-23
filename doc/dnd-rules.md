# Dungeons & Dragons Rules

## Links
For classes and Races: https://dnd5e.wikidot.com/
https://5thsrd.org/rules/
https://www.roll20.net/compendium/dnd5e/Index:Rules
https://www.dndbeyond.com/sources/dnd/basic-rules-2014

The followuing Rules list is an extremely watered down version of the original rule list for sake of clarity:

# D&D 5e Combat Rules (Extremely Compact)

## 1. Math & Dice
* **Modifiers:** (Stat - 10) // 2
* **Advantage (ADV):** Roll 2d20, keep highest.
* **Disadvantage (DIS):** Roll 2d20, keep lowest.
* **Cancellation:** Any ADV + any DIS = 1 normal d20 roll.

## 2. Turn Resources (Reset every round)
* **1 Action:** Attack, Dash, Disengage, Dodge.
* **1 Move:** Distance up to Speed. Can be split up.
* **1 Reaction:** Triggered out-of-turn (e.g., Opportunity Attack).

## 3. Combat Loop
1. **Initiative:** Roll `1d20 + DEX modifier`. Sort highest to lowest.
2. **Round:** Units take turns in order. Skip if HP $\le$ 0.

## 4. Attack Resolution
1. **Range Check:** Melee = 1 tile. Ranged = Normal (normal roll) / Long (DIS) / Out of Range (Impossible).
2. **To-Hit Roll:** `1d20 + Attack Bonus`.
   * Raw 1 = Auto-Miss.
   * Raw 20 = Auto-Crit (Skip AC check, roll double damage dice).
3. **Hit Check:** Hits if `Total Roll >= Target AC`.
4. **Damage:** Subtract `Damage Dice + Modifier` from Target HP. Dead if HP $\le$ 0.

## 5. Grid Laws (1 Tile = 5ft)
* **Diagonals:** Cost 1 tile of movement (1:1 ratio).
* **Collisions:** Can pass through friends, never enemies. Cannot end turn on occupied tiles. Blocked by walls (`#`).
* **Opportunity Attack:** Leaving an enemy's melee range triggers their Reaction for 1 free melee attack.

## 6. Actions List
* **Attack:** Execute Attack Loop.
* **Dash:** Double movement pool for this turn.
* **Disengage:** Moving does not trigger Opportunity Attacks for this turn.
* **Dodge:** Attacks against this unit have DIS until its next turn.

