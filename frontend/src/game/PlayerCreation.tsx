import { useActionState } from "react";

//CONTEXT
import { useAuth } from "@/auth/AuthContext";

//TYPES
import type { PlayerCreationPayload } from "@/api/types";

//SERVICES
import { createPlayer } from "@/api/player";
import { usePlayerStore } from "@/game/store/player-store";

export default function PlayerCreation(){
    const auth = useAuth();
    const setPlayer = usePlayerStore((s) => s.setPlayer);

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

                setPlayer(player);
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