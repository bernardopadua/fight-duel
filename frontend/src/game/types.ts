interface WorldInfo {
    worldName: string;
    worldMinLevel: number;
    worldMaxLevel: number;
};

/*interface Creature {
    id: number
    creatureName: string
    creatureLevel: number
    creatureLife: number
};*/

interface Item {
    id: number
    itemName: string
    itemPower: number
    itemWeight: number
};

interface Player {
    user: number;
    playerName: string;
    playerLevel: number;
    playerExp: number;
    playerPower: number;
    playerStamina: number;
    playerMaxStamina: number;
    playerEquippedWeapon:  number;
    playerEquippedWeaponItem: Item | null;
    playerEquippedArmour:  number | null;
    playerEquippedArmourItem: Item | null;
    playerStatus: string;
    playerMaxWeight: number;
    playerCurrency: number;
    playerLife: number;
    playerMaxLife: number;
    playerWorldInfo: WorldInfo | null
}

export type { Player };