# fking-duel

This is a game about dueling with monster and other players.
- auth
- mmo
- market

## Observations

- camelCase, yes, I use it. It's against PEP 8, I know it. But I feel confortable using it.
  - Is history now. Refactored.

## Status

This project is a few days old, still in early/prototype stage. Requirements are not closed, stuff keeps changing shape almost every commit (models, rules, even how fight works). Don't expect it to be polished or final, it's a work in progress.

### Some ideas
- [ ] Remove item from inventory, get currency in return.

## Sections

### Auth
Login, user

### MMO
world, player, fight

### Market
Trade items, buying items

Each section above is its own Django app (`fkdauth`, `mmo`, `market`), so the domain is separated by app, not just by folder. Inside `mmo`, the game logic itself (damage, level up, drop chance, inventory weight, etc) is separated again in `services/`, as "engines" (`FightEngine`, `PlayerEngine`, `DropEngine`, `PlayerInventoryEngine`...). Views, websocket consumers and celery tasks just call into these engines, they don't hold the rules themselves. `market` for now is just a skeleton, nothing implemented yet.

## Models
### **AUTH**:
#### login (django User Model)
- id
- user
- pass

### **MMO**:
#### world
- id
- worldName
- worldTotalCreatures
- worldMinLevel
- worldMaxLevel
#### worldcreatures
- id
- creatureName
- creatureLevel
- creatureLife
- creatureChanceDrop
#### player
- id
- userId (foreign User)
- playerName
- playerLevel
- playerExp
- playerPower
- playerStamina
- playerEquipedWeapon
- playerEquipedArmour
- playerStatus
- playerMaxWeight (calculated accordingly to player's power)
- playerCurrency
#### playerInventory
- id
- itemId (foreign items)
- playerId (foreign player)
#### items
- id
- itemName
- itemPower
- itemWeight
#### playerfight (table locking fight)
- idCreature (foreign creature)
- idPlayer (foreign player)

### **MARKET**:
#### itemSelling
- itemId (foreign items)
- currencyValue

## Actions
The user can make a login account, create a character (player), enter a world, pick fights, fight, then can buy or sell items. 

#### REST
 - Login/Register
 - Create player
 - Buy items
 - Sell items

#### WebSocket/Channels
 - Fight
 -- All the game logic about fighting will be handled here

### REST vs WebSocket, why both

REST (DRF) is for stuff that happens once or on demand and don't need to be real time: login, register, create player, get player, buy/sell.

WebSocket (Django Channels) is only for the fight. Once a fight starts, everything about it (player attacking, monster attacking, fight ending, item drop) goes through the socket, because both sides need to push updates without the client asking every time. The monster attack side is scheduled with Celery (`countdown`), so it keeps "ticking" on its own and sends the result back through the same fight channel group.

### Fighting
user choose to fight with a creature the fight is locked in database (the creature cannot participate in another fight). 

## Stack

- **Backend**: Django + Django REST Framework (REST endpoints), Django Channels (websocket, the fight), Celery + Redis (background/scheduled jobs: monster attack tick, respawn creatures, recover player status over time), Postgres as the database, Redis also used as cache (attack cooldown).
- **Frontend**: React + TypeScript + Vite.

## About tests (there is none yet)

Right now there is no tests in the project, and that's on purpose for this stage. Requirements are still open and models/engines are being reshaped often (this week alone the inventory logic got refactored, level up got added). Writing tests now would mean rewriting them again in a day or two as things move. Tests will start making sense once the core loop (fight, loot, level up) settles down a bit, right now it would just be extra work for code that won't look the same tomorrow.
