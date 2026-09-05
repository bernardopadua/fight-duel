import { usePlayerStore } from '@/game/store/player-store';

import { PhaserContainer } from '@/game/PhaserContainer';

export default function GameLayout() {
    const player = usePlayerStore((s) => s.player);
    const setCurrency = usePlayerStore((s) => s.setCurrency);

    if (!player) return (<div>Loading player</div>);

    return (
        <div className="relative w-screen h-screen overflow-hidden bg-black select-none">
            {/* 1. phaser*/}
            <PhaserContainer />
            {/* 2. ui / HUD */}
            <div className="absolute inset-0 z-10 pointer-events-none">

                {/* windows ui */}
                <div className="pointer-events-auto absolute top-4 left-4 w-72 bg-slate-900/90 border border-slate-700 rounded-lg p-4 shadow-2xl backdrop-blur-md text-white">
                    <div className="flex justify-between items-center border-b border-slate-700 pb-2 mb-3">
                        <span className="font-bold text-sm tracking-wider uppercase text-amber-400">Player Info</span>
                    </div>
                    <p className="text-sm">Nome: <span className="font-semibold">{player.playerName}</span></p>
                    <p className="text-sm">Level: <span className="font-semibold text-emerald-400">{player.playerLevel}</span></p>
                    <p className="text-sm">Currency: <span className="font-semibold text-yellow-400">{player.playerCurrency}</span></p>
                    <p> <button onClick={() => { setCurrency(player.playerCurrency + 100) }}>TEST</button> </p>
                </div>
                {/* Char selected */}
                <div className="pointer-events-auto absolute top-4 right-4 w-64 bg-slate-900/90 border border-slate-700 rounded-lg p-4 shadow-2xl backdrop-blur-md text-white">
                    <h3 className="font-bold text-sm text-cyan-400 border-b border-slate-700 pb-2 mb-2">Char Selected</h3>
                    <p className="text-xs text-slate-400">...</p>
                </div>
            </div>
        </div>
    );
}