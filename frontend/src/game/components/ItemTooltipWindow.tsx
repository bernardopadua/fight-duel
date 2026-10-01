import { useRef, useLayoutEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// STORE
import { useTooltipStore } from '@/game/store/tooltip-store';

// UTILS
import { getItemSprite } from '@/game/utils/item-utils';
import { ITEM_TYPE } from '@/game/types';

export function ItemTooltipWindow() {
    const { visible, item, coords, extra } = useTooltipStore();
    const tooltipRef = useRef<HTMLDivElement | null>(null);
    const [clampedPos, setClampedPos] = useState({ x: 0, y: 0 });

    useLayoutEffect(() => {
        if (!visible || !item) return;

        const offset = 14;
        const padding = 12;
        const width = tooltipRef.current?.offsetWidth || 220;
        const height = tooltipRef.current?.offsetHeight || 140;

        let x = coords.x + offset;
        let y = coords.y + offset;

        // Invert or clamp if overflowing right edge
        if (x + width + padding > window.innerWidth) {
            x = coords.x - width - offset;
        }

        // Invert or clamp if overflowing bottom edge
        if (y + height + padding > window.innerHeight) {
            y = coords.y - height - offset;
        }

        // Clamp inside window borders
        x = Math.max(padding, Math.min(x, window.innerWidth - width - padding));
        y = Math.max(padding, Math.min(y, window.innerHeight - height - padding));

        setClampedPos({ x, y });
    }, [visible, item, coords.x, coords.y]);

    if (!visible || !item) {
        return null;
    }

    const type = item.itemType?.toLowerCase();
    const isWeapon = type === ITEM_TYPE.WEAPON;
    const isArmour = type === ITEM_TYPE.ARMOUR;
    const isConsumable = type === ITEM_TYPE.CONSUMABLE;

    const getTypeBadge = () => {
        if (isWeapon) {
            return (
                <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded border border-amber-600/50 bg-amber-950/70 text-amber-300">
                    ⚔️ Weapon
                </span>
            );
        }
        if (isArmour) {
            return (
                <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded border border-emerald-600/50 bg-emerald-950/70 text-emerald-300">
                    🛡️ Armour
                </span>
            );
        }
        if (isConsumable) {
            const consType = item.itemConsumableType?.toLowerCase();
            return (
                <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded border border-cyan-600/50 bg-cyan-950/70 text-cyan-300">
                    🧪 {consType ? `${consType.toUpperCase()} POTION` : 'CONSUMABLE'}
                </span>
            );
        }
        return (
            <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded border border-stone-600/50 bg-stone-900 text-stone-300">
                Item
            </span>
        );
    };

    const getStatDisplay = () => {
        if (isWeapon) {
            return {
                label: 'Attack Power',
                value: `+${item.itemPower}`,
                color: 'text-amber-300',
                icon: '⚔️',
            };
        }
        if (isArmour) {
            return {
                label: 'Defense Power',
                value: `+${item.itemPower}`,
                color: 'text-emerald-300',
                icon: '🛡️',
            };
        }
        if (isConsumable) {
            const isLife = item.itemConsumableType === 'life';
            return {
                label: isLife ? 'Restores Life' : 'Restores Stamina',
                value: `+${item.itemPower}`,
                color: isLife ? 'text-rose-400' : 'text-cyan-300',
                icon: isLife ? '❤️' : '⚡',
            };
        }
        return {
            label: 'Power',
            value: `+${item.itemPower}`,
            color: 'text-amber-200',
            icon: '✨',
        };
    };

    const stat = getStatDisplay();

    return (
        <AnimatePresence>
            <motion.div
                ref={tooltipRef}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.1, ease: 'easeOut' }}
                style={{
                    position: 'fixed',
                    left: `${clampedPos.x}px`,
                    top: `${clampedPos.y}px`,
                }}
                className="pointer-events-none z-50 min-w-[210px] max-w-[260px] rounded border-2 border-amber-700/90 bg-gradient-to-b from-stone-900/98 via-neutral-950/98 to-black/98 p-3 text-stone-200 shadow-[0_8px_24px_rgba(0,0,0,0.85)] ring-1 ring-amber-500/40 backdrop-blur-md"
            >
                {/* Diamond Corner Accents matching RPG Window */}
                <span className="absolute -top-1 -left-1 h-2 w-2 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_4px_#f59e0b]" />
                <span className="absolute -top-1 -right-1 h-2 w-2 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_4px_#f59e0b]" />
                <span className="absolute -bottom-1 -left-1 h-2 w-2 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_4px_#f59e0b]" />
                <span className="absolute -bottom-1 -right-1 h-2 w-2 rotate-45 border border-amber-300 bg-amber-600 shadow-[0_0_4px_#f59e0b]" />

                {/* Header: Sprite + Name + Badge */}
                <div className="flex items-start gap-2.5 border-b border-amber-700/50 pb-2 mb-2">
                    <div className="relative w-10 h-10 flex-shrink-0 flex items-center justify-center rounded bg-stone-950/90 border border-amber-800/60 p-1 shadow-inner">
                        <img
                            src={getItemSprite(item)}
                            alt={item.itemName}
                            className="w-full h-full object-contain [image-rendering:pixelated]"
                        />
                    </div>

                    <div className="flex flex-col min-w-0 flex-1">
                        <span className="font-['Cinzel'] text-xs font-bold tracking-wider text-amber-200 truncate drop-shadow">
                            {item.itemName}
                        </span>
                        <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                            {getTypeBadge()}
                            {extra?.isEquipped && (
                                <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded border border-emerald-500/60 bg-emerald-950/80 text-emerald-300">
                                    Equipped
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Stats Section */}
                <div className="flex flex-col gap-1.5 text-[11px]">
                    <div className="flex items-center justify-between rounded bg-stone-950/80 px-2 py-1 border border-stone-800/80">
                        <span className="text-stone-400 flex items-center gap-1">
                            <span>{stat.icon}</span>
                            <span>{stat.label}</span>
                        </span>
                        <span className={`font-bold ${stat.color}`}>
                            {stat.value}
                        </span>
                    </div>

                    <div className="flex items-center justify-between rounded bg-stone-950/80 px-2 py-1 border border-stone-800/80">
                        <span className="text-stone-400 flex items-center gap-1">
                            <span>⚖️</span>
                            <span>Weight</span>
                        </span>
                        <span className="font-semibold text-stone-200">
                            {item.itemWeight ?? 0}
                        </span>
                    </div>
                </div>

                {/* Extra hint or subtext if provided */}
                {extra?.hint && (
                    <div className="mt-2 pt-1.5 border-t border-stone-800/80 text-[10px] text-stone-400 italic text-center">
                        {extra.hint}
                    </div>
                )}
            </motion.div>
        </AnimatePresence>
    );
}
