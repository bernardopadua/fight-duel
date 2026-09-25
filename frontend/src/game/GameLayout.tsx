import { useRef, useEffect } from 'react';

//EVENTS
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

//STORE
import { useDropStore } from '@/game/store/drop-store';

//COMPONENTS
import { PhaserContainer } from '@/game/PhaserContainer';
import { WindowRPG } from '@/game/components/WindowRPG';
import { PlayerDetails, PlayerDetailsRightSide } from '@/game/components/PlayerDetails';
import { DropItems } from '@/game/components/DropItems';

export default function GameLayout() {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const { items, setItems } = useDropStore();

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

            {items.length > 0 && (
                <WindowRPG 
                    title='Drop Items' 
                    icon='📦' 
                    rightSide={null}
                    parentContainerRef={containerRef}
                >
                    <DropItems 
                        items={items}
                        onLoot={(selectedItems) => {
                            setItems(items.filter((item) => !selectedItems.includes(item)));
                        }}
                    />
                </WindowRPG>
            )}
        </div>
    );
}