//STORE
import { usePlayerStore } from '@/game/store/player-store';
import { useDropStore } from '@/game/store/drop-store';
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
    const { open, toggle, setInitialPosition } = useUIStore();

    if (!player) return null;

    return (
        <div>
            <div className="space-y-2.5 text-sm">
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