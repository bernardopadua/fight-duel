import { useState } from 'react';

//STORE
import { usePlayerStore } from '@/game/store/player-store';
import { useUIStore } from '@/game/store/ui-store';

export function PlayerDetailsRightSide(){
    const player = usePlayerStore((s) => s.player);

    if (!player) return null;

    return (
        <span className="rounded border border-amber-600/60 bg-amber-950/80 px-2 py-0.5 text-xs font-bold text-amber-300">
            LV. {player.playerLevel}
        </span>
    );
}

export function PlayerDetails(){
    const player = usePlayerStore((s) => s.player);
    const { open } = useUIStore();

    const [timeLeft, setTimeLeft] = useState<number | undefined>(undefined);

    if (!player) return null;

    const isDead = player.playerStatus === 'dead' || player.playerLife <= 0;

    return (
        <div>
            <div className="space-y-2.5 text-sm">

                {isDead && (
                    <div className="flex items-center justify-between p-2.5 rounded bg-red-950/70 border border-red-600/70 text-red-200 shadow-[0_0_12px_rgba(220,38,38,0.25)]">
                        <div className="flex items-center gap-2">
                            <span className="text-base animate-pulse">💀</span>
                            <div className="flex flex-col">
                                <span className="text-xs font-bold uppercase tracking-wider text-red-400">
                                    Dead
                                </span>
                                <span className="text-[10px] text-red-300/80">
                                    {timeLeft !== undefined && timeLeft > 0 ? 'Reviving soon...' : 'Waiting for revival'}
                                </span>
                            </div>
                        </div>

                        {timeLeft !== undefined && timeLeft > 0 && (
                            <div className="flex items-center gap-1 font-mono font-bold text-xs bg-red-900/80 px-2 py-1 rounded border border-red-700/80 text-red-100 shadow-inner">
                                <span>⏳</span>
                                <span>{Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}</span>
                            </div>
                        )}
                    </div>
                )}

                <div className="flex justify-between items-center rounded bg-stone-900/60 px-2.5 py-1.5 border border-stone-800">
                    <span className="text-xs text-stone-400 font-medium">Nome</span>
                    <span className="font-semibold text-amber-100">{player.playerName}</span>
                </div>

                <div className="flex justify-between items-center rounded bg-stone-900/60 px-2.5 py-1.5 border border-stone-800">
                    <span className="text-xs text-stone-400 font-medium">Ouro</span>
                    <div className="flex items-center gap-1 font-bold text-yellow-400">
                    <span>🪙</span>
                    <span>{player.playerCurrency.toLocaleString()}</span>
                    </div>
                </div>

                <button 
                    type="button"
                    onClick={() => open('playerStats')}
                    className="w-full mt-2 rounded border border-amber-500/80 bg-gradient-to-b from-amber-600 via-amber-700 to-amber-900 py-1.5 text-xs font-bold tracking-wider text-amber-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5"
                >
                    ⚔️ Player Stats
                </button>

                <button 
                    type="button"
                    onClick={() => open('inventory')}
                    className="w-full mt-2 rounded border border-amber-500/80 bg-gradient-to-b from-amber-600 via-amber-700 to-amber-900 py-1.5 text-xs font-bold tracking-wider text-amber-100 uppercase shadow-[0_2px_4px_rgba(0,0,0,0.5)] transition-all hover:brightness-110 active:translate-y-0.5"
                >
                    🎒 Player Inventory
                </button>
                
            </div>
        </div>
    );
}