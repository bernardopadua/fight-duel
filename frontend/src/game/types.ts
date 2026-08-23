interface Creature {
    id: number
    creatureName: string
    creatureLevel: number
    creatureLife: number
};

interface Item {
    id: number
    itemName: string
    itemPower: number
    itemWeight: number
};

interface Player {
    id: number
    playerName: string
    playerLevel: number
    playerExp: number
    playerPower: number
    playerStamina: number
    playerEquipedWeapon: Item | null
    playerEquipedArmour: Item | null
    playerStatus: string
    playerMaxWeight: number
    playerCurrency: number
}

export type { Player };