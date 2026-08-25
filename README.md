# fking-duel

## TODO
 - Refactoring orphan item. Add a created date and clean a day old orphans or maybe hours.

This is a game about dueling with monster and other players.
- auth
- mmo
- market

## Sections
### Auth
Login, user
### MMO
world, player, fight
### Market
Trade items, buying items

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
 

### Fighting
user choose to fight with a creature the fight is locked in database (the creature cannot participate in another fight). 