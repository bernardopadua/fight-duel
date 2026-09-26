import { useRef, useEffect } from 'react';

//EVENTS
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

//AUTH
import { useAuth } from '@/auth/auth-context';

//SERVICES
import { useGameContext } from '@/game/game-context';

//STORE
import { useUIStore } from '@/game/store/ui-store';

//COMPONENTS
import { PhaserContainer } from '@/game/PhaserContainer';
import { WindowRPG } from '@/game/components/WindowRPG';
import { PlayerDetails, PlayerDetailsRightSide } from '@/game/components/PlayerDetails';
import { DropItems } from '@/game/components/DropItems';
import { PlayerInventory } from '@/game/components/PlayerInventory';
import { PlayerStats } from '@/game/components/PlayerStats';

export default function GameLayout() {
    const auth = useAuth();
    const services = useGameContext();
    const containerRef = useRef<HTMLDivElement | null>(null);
    const { windows } = useUIStore(); 

    useEffect(()=>{
        const updatePlayer = () => {
            services.playerService.getPlayer(auth.token);
        };
        EventBus.on(GAME_EVENTS.UPDATE_PLAYER, updatePlayer);

        return () => {
            EventBus.off(GAME_EVENTS.UPDATE_PLAYER, updatePlayer);
        }
    },[]);

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

            {windows.playerStats.open && (
                <WindowRPG
                    title='Player Stats'
                    icon='⚔️'
                    rightSide={null}
                    parentContainerRef={containerRef}
                    onClose={() => useUIStore.getState().close('playerStats')}
                >
                    <PlayerStats />
                </WindowRPG>
            )}

            {windows.dropItems.open && (
                <WindowRPG 
                    title='Drop Items' 
                    icon='📦' 
                    rightSide={null}
                    parentContainerRef={containerRef}
                    initialPosition={windows.dropItems.initialPosition}
                >
                    <DropItems />
                </WindowRPG>
            )}

            {windows.inventory.open && (
                <WindowRPG
                    title='Player Inventory'
                    icon='🎒'
                    rightSide={null}
                    parentContainerRef={containerRef}
                    onClose={() => useUIStore.getState().close('inventory')}
                >
                    <PlayerInventory />
                </WindowRPG>
            )}
        </div>
    );
}