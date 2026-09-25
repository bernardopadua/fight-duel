//REACT
import { useState } from 'react';

//SERVICES
import { useGameContext } from '@/game/game-context';

//STORE
import { usePlayerInventoryStore, type PlayerInventoryItem } from '@/game/store/player-inventory-store';

//TYPES
import { ITEM_TYPE } from '@/game/types';

function getItemSprite(item: PlayerInventoryItem): string {
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

export function PlayerInventory() {
    const items = usePlayerInventoryStore((s) => s.items);

    const { playerInventoryService } = useGameContext();

    const [selectedItem, setSelectedItem] = useState<PlayerInventoryItem | null>(null);

    const consumables = items.filter((i) => i.itemType?.toLowerCase() === 'consumable');
    const nonConsumables = items.filter((i) => i.itemType?.toLowerCase() !== 'consumable');

    const handleSelect = (item: PlayerInventoryItem) => {
        setSelectedItem((prev) => (prev?.id === item.id ? null : item));
    };

    const handleUseItem = () => {
        if (!selectedItem) return;
        playerInventoryService.useItem(selectedItem);
        setSelectedItem(null);
    };

    const handleEquipItem = () => {
        if (!selectedItem) return;
        playerInventoryService.equipItem(selectedItem);
        setSelectedItem(null);
    };

    const handleSalvageItem = () => {
        if (!selectedItem) return;
        playerInventoryService.salvageItem(selectedItem);
        setSelectedItem(null);
    };

    return (
        <div className="flex flex-col gap-3 text-stone-200">
            <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-bold tracking-widest text-amber-400 uppercase">
                    Equipment ({nonConsumables.length})
                </span>
                <div className="flex flex-wrap gap-1.5 p-2 bg-stone-950/80 rounded border border-stone-800/80 min-h-[50px] max-h-36 overflow-y-auto">
                    {nonConsumables.length === 0 ? (
                        <span className="text-[11px] text-stone-500 italic m-auto">No equipment</span>
                    ) : (
                        nonConsumables.map((item) => {
                            const isSelected = selectedItem?.id === item.id;
                            return (
                                <button
                                    key={item.id}
                                    type="button"
                                    title={`${item.itemName} | Power: ${item.itemPower}`}
                                    onClick={() => handleSelect(item)}
                                    className={`relative w-11 h-11 flex items-center justify-center rounded cursor-pointer transition-all p-1
                                        ${isSelected 
                                            ? 'border border-amber-300 bg-amber-900/60 ring-2 ring-amber-400/90 shadow-[0_0_8px_#f59e0b]' 
                                            : 'border border-stone-700/80 bg-stone-900/80 hover:border-amber-500/60 hover:bg-stone-800'
                                        }`}
                                >
                                    <img
                                        src={getItemSprite(item)}
                                        alt={item.itemName}
                                        className="w-full h-full object-contain [image-rendering:pixelated] select-none pointer-events-none"
                                    />
                                </button>
                            );
                        })
                    )}
                </div>
            </div>

            <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-bold tracking-widest text-amber-400 uppercase">
                    Consumables ({consumables.length})
                </span>
                <div className="flex flex-wrap gap-1.5 p-2 bg-stone-950/80 rounded border border-stone-800/80 min-h-[50px] max-h-36 overflow-y-auto">
                    {consumables.length === 0 ? (
                        <span className="text-[11px] text-stone-500 italic m-auto">No consumables</span>
                    ) : (
                        consumables.map((item) => {
                            const isSelected = selectedItem?.id === item.id;
                            return (
                                <button
                                    key={item.id}
                                    type="button"
                                    title={`${item.itemName} | Recovery: +${item.itemPower}`}
                                    onClick={() => handleSelect(item)}
                                    className={`relative w-11 h-11 flex items-center justify-center rounded cursor-pointer transition-all p-1
                                        ${isSelected 
                                            ? 'border border-amber-300 bg-amber-900/60 ring-2 ring-amber-400/90 shadow-[0_0_8px_#f59e0b]' 
                                            : 'border border-stone-700/80 bg-stone-900/80 hover:border-amber-500/60 hover:bg-stone-800'
                                        }`}
                                >
                                    <img
                                        src={getItemSprite(item)}
                                        alt={item.itemName}
                                        className="w-full h-full object-contain [image-rendering:pixelated] select-none pointer-events-none"
                                    />
                                    <span className="absolute bottom-0.5 right-0.5 text-[9px] font-bold text-emerald-300 bg-stone-950/90 px-1 py-0.2 rounded border border-emerald-800/60 leading-none">
                                        +{item.itemPower}
                                    </span>
                                </button>
                            );
                        })
                    )}
                </div>
            </div>

            <div className="flex gap-2 pt-1 border-t border-amber-700/40">
                {selectedItem?.itemType === ITEM_TYPE.CONSUMABLE ? (
                    <button
                        type="button"
                        onClick={handleUseItem}
                        className="flex-1 rounded border border-emerald-500/80 bg-gradient-to-b from-emerald-600 via-emerald-700 to-emerald-900 py-1.5 text-xs font-bold tracking-wider text-emerald-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5 cursor-pointer"
                    >
                        Use
                    </button>
                ) : (
                    <button
                        type="button"
                        disabled={!selectedItem}
                        onClick={handleEquipItem}
                        className="flex-1 rounded border border-amber-500/80 bg-gradient-to-b from-amber-600 via-amber-700 to-amber-900 py-1.5 text-xs font-bold tracking-wider text-amber-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                    >
                        Equip
                    </button>
                )}

                <button
                    type="button"
                    disabled={!selectedItem}
                    onClick={handleSalvageItem}
                    className="flex-1 rounded border border-red-500/80 bg-gradient-to-b from-red-700 via-red-800 to-red-950 py-1.5 text-xs font-bold tracking-wider text-red-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                    Salvage
                </button>
            </div>
        </div>
    );
}
