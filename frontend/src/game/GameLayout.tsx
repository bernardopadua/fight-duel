import type { Player } from "./types";

export default function GameLayout({ player }: { player: Player }) {
    return (
        <div className="grid grid-cols-2 grid-rows-[auto_1fr] h-screen">
            <aside className="border p-4">
                User info + Inventário
                <p>Player: {player.playerName}</p>
                <p>Level: {player.playerLevel}</p>
                <p>Currency: {player.playerCurrency}</p>
            </aside>
            <aside className="border p-4">Char selected</aside>
            <div id="phaser-container" className="col-span-2 bg-black" />
        </div>
    );
}