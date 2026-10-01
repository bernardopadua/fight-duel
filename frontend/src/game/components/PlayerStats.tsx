import { useEffect } from 'react';
import { usePlayerStore } from '@/game/store/player-store';
import { useTooltipStore } from '@/game/store/tooltip-store';
import { ITEM_TYPE } from '@/game/types';
import type { Item } from '@/game/store/store-types';

export function PlayerStats() {
    const player = usePlayerStore((s) => s.player);
    const showTooltip = useTooltipStore((s) => s.showTooltip);
    const updateCoords = useTooltipStore((s) => s.updateCoords);
    const hideTooltip = useTooltipStore((s) => s.hideTooltip);

    useEffect(() => {
        return () => {
            hideTooltip();
        };
    }, [hideTooltip]);

    if (!player) {
        return (
            <div className="py-4 text-center text-xs text-stone-500 italic">
                Player not loaded
            </div>
        );
    }

    const basePower = player.playerPower ?? 0;
    const weapon = player.playerEquippedWeaponItem;
    const armour = player.playerEquippedArmourItem;

    const weaponPower = weapon?.itemPower ?? 0;
    const armourPower = armour?.itemPower ?? 0;
    const totalPower = basePower + weaponPower + armourPower;

    return (
        <div className="flex flex-col gap-3 text-stone-200">
            <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                    <span className="text-[10px] font-bold tracking-widest text-amber-400 uppercase">
                        Attributes
                    </span>

                    <div className="space-y-1 text-xs">
                        <div className="flex justify-between items-center px-2 py-1 rounded bg-stone-950/80 border border-stone-800/80">
                            <span className="text-[9px] text-stone-400">Level</span>
                            <span className="font-bold text-amber-300">{player.playerLevel}</span>
                        </div>

                        <div className="flex justify-between items-center px-2 py-1 rounded bg-stone-950/80 border border-stone-800/80">
                            <span className="text-[9px] text-stone-400">Life</span>
                            <span className="font-bold text-red-400">
                                {player.playerLife} <span className="text-stone-500 text-[9px]">/ {player.playerMaxLife}</span>
                            </span>
                        </div>

                        <div className="flex justify-between items-center px-2 py-1 rounded bg-stone-950/80 border border-stone-800/80">
                            <span className="text-[9px] text-stone-400">Stamina</span>
                            <span className="font-bold text-emerald-400">
                                {player.playerStamina} <span className="text-stone-500 text-[9px]">/ {player.playerMaxStamina}</span>
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col gap-1.5 items-center">
                    <span className="text-[10px] font-bold tracking-widest text-amber-400 uppercase">
                        Equipped
                    </span>

                    <div className="flex gap-2">
                        {/* Weapon Slot */}
                        <div className="flex flex-col items-center gap-1">
                            <div 
                                onMouseEnter={(e) => {
                                    if (weapon) {
                                        const item: Item = {
                                            ...weapon,
                                            itemType: (weapon as any).itemType || ITEM_TYPE.WEAPON,
                                            itemConsumableType: null,
                                        };
                                        showTooltip(item, { x: e.clientX, y: e.clientY }, { isEquipped: true });
                                    }
                                }}
                                onMouseMove={(e) => {
                                    if (weapon) updateCoords({ x: e.clientX, y: e.clientY });
                                }}
                                onMouseLeave={() => hideTooltip()}
                                className={`w-11 h-11 flex items-center justify-center rounded p-1 transition-all
                                    ${weapon 
                                        ? 'border border-amber-500/80 bg-stone-900/90 shadow-[0_0_6px_rgba(245,158,11,0.2)] cursor-pointer' 
                                        : 'border border-dashed border-stone-700/80 bg-stone-950/60'
                                    }`}
                            >
                                {weapon ? (
                                    <img
                                        src="/sprites/items/weapon.png"
                                        alt={weapon.itemName}
                                        className="w-full h-full object-contain [image-rendering:pixelated] select-none pointer-events-none"
                                    />
                                ) : (
                                    <span className="text-sm opacity-30 select-none">🗡️</span>
                                )}
                            </div>
                            <span className="text-[10px] font-semibold text-amber-200/90 leading-none">
                                PWR: {weaponPower}
                            </span>
                        </div>

                        {/* Armour Slot */}
                        <div className="flex flex-col items-center gap-1">
                            <div 
                                onMouseEnter={(e) => {
                                    if (armour) {
                                        const item: Item = {
                                            ...armour,
                                            itemType: (armour as any).itemType || ITEM_TYPE.ARMOUR,
                                            itemConsumableType: null,
                                        };
                                        showTooltip(item, { x: e.clientX, y: e.clientY }, { isEquipped: true });
                                    }
                                }}
                                onMouseMove={(e) => {
                                    if (armour) updateCoords({ x: e.clientX, y: e.clientY });
                                }}
                                onMouseLeave={() => hideTooltip()}
                                className={`w-11 h-11 flex items-center justify-center rounded p-1 transition-all
                                    ${armour 
                                        ? 'border border-amber-500/80 bg-stone-900/90 shadow-[0_0_6px_rgba(245,158,11,0.2)] cursor-pointer' 
                                        : 'border border-dashed border-stone-700/80 bg-stone-950/60'
                                    }`}
                            >
                                {armour ? (
                                    <img
                                        src="/sprites/items/armour.png"
                                        alt={armour.itemName}
                                        className="w-full h-full object-contain [image-rendering:pixelated] select-none pointer-events-none"
                                    />
                                ) : (
                                    <span className="text-sm opacity-30 select-none">🛡️</span>
                                )}
                            </div>
                            <span className="text-[10px] font-semibold text-amber-200/90 leading-none">
                                PWR: {armourPower}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="rounded border border-amber-600/40 bg-gradient-to-b from-stone-950/90 to-stone-900/90 p-2 text-center shadow-inner">
                <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-amber-300">
                    <span>⚔️</span>
                    <span className="uppercase tracking-wider">Total Power:</span>
                    <span className="text-amber-100 text-sm">{totalPower}</span>
                </div>

                {/* Explicit Formula */}
                <div className="mt-1 flex items-center justify-center gap-1 text-[10px] text-stone-400">
                    <span className="bg-stone-900/90 px-1 py-0.5 rounded border border-stone-800 text-stone-300" title="Player Base Power">
                        Base: {basePower}
                    </span>
                    <span>+</span>
                    <span className="bg-stone-900/90 px-1 py-0.5 rounded border border-stone-800 text-amber-300" title="Weapon Power">
                        Wpn: {weaponPower}
                    </span>
                    <span>+</span>
                    <span className="bg-stone-900/90 px-1 py-0.5 rounded border border-stone-800 text-amber-300" title="Armour Power">
                        Arm: {armourPower}
                    </span>
                </div>
            </div>
        </div>
    );
}
