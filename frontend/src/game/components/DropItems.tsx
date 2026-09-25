import { useState } from 'react';

//TYPES
import type { DropItem } from '@/game/store/drop-store';

//INTERFACE
interface DropItemsProps {
    items?: DropItem[];
    onLoot?: (selectedItems: DropItem[]) => void;
}

function getItemSprite(item: DropItem): string {
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

export function DropItems({ items = [], onLoot }: DropItemsProps) {
    const [selectedIds, setSelectedIds] = useState<number[]>([]);

    const toggleItem = (id: number) => {
        setSelectedIds((prev) =>
            prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id]
        );
    };

    const toggleAll = () => {
        if (selectedIds.length === items.length) {
            setSelectedIds([]);
        } else {
            setSelectedIds(items.map((item) => item.id));
        }
    };

    const handleLoot = () => {
        const selectedItems = items.filter((item) => selectedIds.includes(item.id));
        //onLoot?.(selectedItems);
    };

    return (
        <div className="flex flex-col gap-2.5">
            <div className="flex items-center justify-between text-[11px] text-stone-400 px-0.5">
                <span>
                    Selected: <strong className="text-amber-300">{selectedIds.length}</strong>/{items.length}
                </span>
                {items.length > 0 && (
                    <button
                        type="button"
                        onClick={toggleAll}
                        className="text-[10px] text-amber-400 hover:text-amber-300 underline uppercase tracking-wider cursor-pointer"
                    >
                        {selectedIds.length === items.length ? 'Deselect All' : 'Select All'}
                    </button>
                )}
            </div>

            <div className="flex flex-wrap gap-1.5 p-2 bg-stone-950/80 rounded border border-stone-800/80 min-h-[56px] max-h-48 overflow-y-auto">
                {items.length === 0 ? (
                    <span className="text-[11px] text-stone-500 italic m-auto">No items dropped</span>
                ) : (
                    items.map((item) => {
                        const isSelected = selectedIds.includes(item.id);
                        return (
                            <button
                                key={item.id}
                                type="button"
                                title={`${item.itemName} | Power: ${item.itemPower ?? 0} | Weight: ${item.itemWeight ?? 0}`}
                                onClick={() => toggleItem(item.id)}
                                className={`w-16 h-16 flex items-center justify-center rounded cursor-pointer transition-all p-0.5
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

            <button
                type="button"
                disabled={selectedIds.length === 0}
                onClick={handleLoot}
                className="w-full rounded border border-amber-500/80 bg-gradient-to-b from-amber-600 via-amber-700 to-amber-900 py-1.5 text-xs font-bold tracking-wider text-amber-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
                {selectedIds.length > 0 ? `Loot (${selectedIds.length})` : 'Loot'}
            </button>
        </div>
    );
}