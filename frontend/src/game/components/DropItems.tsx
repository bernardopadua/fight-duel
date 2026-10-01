import { useState, useEffect } from 'react';

//CONTEXT
import { useGameContext } from '@/game/game-context';

//STORE
import { useDropStore } from '@/game/store/drop-store';
import { useUIStore } from '@/game/store/ui-store';
import { usePlayerStore } from '@/game/store/player-store';
import { usePlayerInventoryStore } from '@/game/store/player-inventory-store';
import { useTooltipStore } from '@/game/store/tooltip-store';

// UTILS
import { getItemSprite } from '@/game/utils/item-utils';

export function DropItems() {
    const items = useDropStore((s) => s.items);
    const setDropItems = useDropStore((s) => s.setItems);
    const player = usePlayerStore((s) => s.player);
    const itemsInventory = usePlayerInventoryStore((s) => s.items);
    const { playerService } = useGameContext();
    const [selectedIds, setSelectedIds] = useState<number[]>([]);

    const showTooltip = useTooltipStore((s) => s.showTooltip);
    const updateCoords = useTooltipStore((s) => s.updateCoords);
    const hideTooltip = useTooltipStore((s) => s.hideTooltip);

    useEffect(() => {
        return () => {
            hideTooltip();
        };
    }, [hideTooltip]);

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
        const totalWeight = selectedItems.reduce((acc, item) => acc + (item.itemWeight ?? 0), 0);
        const totalInventoryWeight = itemsInventory.reduce((acc, item) => acc + (item.itemWeight ?? 0), 0);
        const totalCarrying = player.playerMaxWeight - totalInventoryWeight;

        if(totalWeight > totalCarrying){
            alert('Too much weight. Empty some items from your inventory.');
            return;
        };
        playerService.lootItems(selectedItems);
        hideTooltip();

        if (selectedItems.length == items.length){
            setDropItems([]);
            useUIStore.getState().close('dropItems');
        } else if (selectedItems.length < items.length){
            setDropItems(items.filter((item) => !selectedIds.includes(item.id)));
        };
        setSelectedIds([]);
    };

    const handleDiscard = () => {
        hideTooltip();
        useDropStore.getState().setItems([]);
        setSelectedIds([]);
        useUIStore.getState().close('dropItems');
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
                                onClick={() => toggleItem(item.id)}
                                onMouseEnter={(e) =>
                                    showTooltip(item, { x: e.clientX, y: e.clientY }, {
                                        hint: isSelected ? 'Click to deselect' : 'Click to select for loot'
                                    })
                                }
                                onMouseMove={(e) => updateCoords({ x: e.clientX, y: e.clientY })}
                                onMouseLeave={() => hideTooltip()}
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

            <div className="flex gap-2 pt-1 border-t border-amber-700/40">
                <button
                    type="button"
                    disabled={selectedIds.length === 0}
                    onClick={handleLoot}
                    className="flex-1 rounded border border-amber-500/80 bg-gradient-to-b from-amber-600 via-amber-700 to-amber-900 py-1.5 text-xs font-bold tracking-wider text-amber-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                    {selectedIds.length > 0 ? `Loot (${selectedIds.length})` : 'Loot'}
                </button>
                
                <button
                    type="button"
                    onClick={handleDiscard}
                    className="flex-1 rounded border border-red-500/80 bg-gradient-to-b from-red-700 via-red-800 to-red-950 py-1.5 text-xs font-bold tracking-wider text-red-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                    Discard
                </button>
            </div>
        </div>
    );
}