## Gameplay GUIDE

Player is the base entity in the game. Everything revolves around the player. When the connection to the websocket occurs the player recover it's state and is ready to play around.

Somethings use cases:

- Player has to enter in a world, move around to find fights.
- Player has to be in a world to find fights. The player can find fights against any other players.
- Currently the player can find fights against any level in the range level of the world. Matchmaking tries to be fair making encounters that are somewhat balanced in creature level and player level.
- Currently the move action is the base of actions (to fight), you have to move around to find fights and other players.