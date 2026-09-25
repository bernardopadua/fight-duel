//ITEM TYPES
import type { ItemType, ItemConsumableType } from '@/game/types';

export interface Item {
    id: number;
    itemName: string;
    itemPower: number;
    itemWeight: number;
    itemType: ItemType;
    itemConsumableType: ItemConsumableType | null;
}