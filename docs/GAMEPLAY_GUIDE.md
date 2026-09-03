## Gameplay GUIDE

Player is the base entity in the game. Everything revolves around the player. When the connection to the websocket occurs the player recover it's state and is ready to play around.

### Somethings use cases:

- Player has to enter in a world, move around to find fights.
- Player has to be in a world to find fights. The player can find fights against any other players.
- Currently, the player can find fights against any level in the range level of the world. Matchmaking tries to be fair making encounters that are somewhat balanced in creature level (player level in the future).
- Currently, the `move` action is the base of actions (to fight), you have to move around to find fights and other players.
- Player starts with 10 power points that is the base of damage calculation. Players start with 100 life points.
- Player each weapon and amour gives a boost of Power, that will count to the final damage power. Amour also counts to the total power.
- Armour counts to defense power against total power damage from another player and creatures.
- Player spends stamina in each attack, more weight the player has, more stamina the player spends.
- Player regains stamina over time (in ticks of the world, base on level and power).

### Play sequence:

1. Create user
2. Create player
3. Get player
4. Enter World
5. Move / Find Fight
6. Attack / Flee
7. Get reward

### What to do if nothing happens:

- Are you moving and no fight ?
  - Are you in a world ?
- Are you attacking with no return ?
  - Do you have stamina ?
