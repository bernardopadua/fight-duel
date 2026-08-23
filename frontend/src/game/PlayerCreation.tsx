import { useActionState } from "react";

import { useAuth } from "../auth/AuthContext";

import type { Player } from "./types";
import type { PlayerCreationPayload } from "../api/types";

import { createPlayer } from "../api/player";

export default function PlayerCreation({ onPlayerCreation }: { onPlayerCreation: (p: Player) => void } ){
    const auth = useAuth();
    const [errorState, formAction, isPending] = useActionState(
        async (_prevState: string | null, formData: FormData) : Promise<string | null> => {
            const playerName = formData.get("playerName")?.toString();

            if (!playerName || playerName.trim().length < 3){
                return "Player name must be at least 3 characters long";
            }
            
            const payload: PlayerCreationPayload = {
                playerName: playerName
            };

            try {
                const player = await createPlayer(auth.token!, payload);
                if (!player) {
                    return "Error creating player";
                }

                onPlayerCreation(player);
            } catch (err){
                console.error(err);
                return "Error creating player. Contact support.";
            }
           
            return null;
    }, null);

    return (
        <div>
            <h1>Create Character</h1>
            {errorState && <p>{errorState}</p>}
            <form action={formAction}>
                <input name="playerName" 
                    type="text" placeholder="playerName" 
                />
                <button type="submit" disabled={isPending}>
                    {isPending ? "Creating..." : "Create"}
                </button>
            </form>
        </div>
    );
}