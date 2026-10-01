import type { Item } from '@/game/store/store-types';

export function getItemSprite(item: Item): string {
    const type = item.itemType?.toLowerCase();
    if (type === 'consumable' && item.itemConsumableType) {
        return `/sprites/items/${item.itemConsumableType.toLowerCase()}.png`;
    }
    if (type === 'armour' || type === 'armor') {
        return '/sprites/items/armour.png';
    }
    if (type === 'weapon') {
        return '/sprites/items/weapon.png';
    }
    return `/sprites/items/${type || 'weapon'}.png`;
}
