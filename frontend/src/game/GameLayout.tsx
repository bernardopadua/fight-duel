import { useRef } from 'react';

import { PhaserContainer } from '@/game/PhaserContainer';
import { WindowRPG } from '@/game/components/WindowRPG';
import { PlayerDetails, PlayerDetailsRightSide } from '@/game/components/PlayerDetails';

export default function GameLayout() {
    const containerRef = useRef<HTMLDivElement | null>(null);
    
    return (
        <div ref={containerRef} className="relative w-screen h-screen overflow-hidden bg-black select-none">
            <PhaserContainer />

            <WindowRPG 
                title='Player Profile' 
                icon='🛡️' 
                rightSide={<PlayerDetailsRightSide />}
                parentContainerRef={containerRef}
            >
                <PlayerDetails />
            </WindowRPG>
        </div>
    );
}