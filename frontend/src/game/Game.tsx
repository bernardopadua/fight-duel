//REACT
import { useEffect } from 'react';

//CONTEXT
import { useAuth } from '@/auth/auth-context';
import { useGameContext } from '@/game/game-context';

// HOOKS
import { useWebSocketStatus } from '@/game/services/ws-service';

// GAME COMPONENTS
import GameLoggedIn from '@/game/GameLoggedIn';

function Game(){
    const auth = useAuth();
    const services = useGameContext();
    const wsStatus = useWebSocketStatus(services.websocketService);

    useEffect(()=>{
        if(wsStatus === "error" || wsStatus === "disconnected"){
            auth.logout();
        }
    }, [auth, wsStatus]);

    if(wsStatus === "connecting")
        return (<h2>Game is connecting...</h2>)

    if(wsStatus === "error" || wsStatus === "disconnected"){
        return (<h2>Game disconnected...</h2>)
    }

    return <GameLoggedIn />;
};

export default Game;