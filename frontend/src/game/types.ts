interface WorldInfo {
    id: number;
    worldName: string;
    worldMinLevel: number;
    worldMaxLevel: number;
};

export const ITEM_TYPE = {
    ARMOUR: 'armour',
    WEAPON: 'weapon',
    CONSUMABLE: 'consumable'
};

export const ITEM_CONSUMABLE_TYPE = {
    LIFE: 'life',
    STAMINA: 'stamina'
};

export type ItemConsumableType = typeof ITEM_CONSUMABLE_TYPE[keyof typeof ITEM_CONSUMABLE_TYPE];
export type ItemType = typeof ITEM_TYPE[keyof typeof ITEM_TYPE];

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

export type { Player, WorldInfo };