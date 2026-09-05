import { getWorlds } from '@/api/world';

import { useWorldStore } from '@/game/store/world-store';

interface WorldService {
    fetchWorlds: (token: string) => Promise<boolean>;
};

function createWorldService(): WorldService {
    return {
        fetchWorlds: async (token: string) => {
            const worlds = await getWorlds(token);
            if (worlds) {
                useWorldStore.getState().setWorlds(worlds);
                return true;
            }
            return false;
        }
    };
};

export { createWorldService, type WorldService };
