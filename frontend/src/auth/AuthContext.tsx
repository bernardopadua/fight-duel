import { useState } from 'react';
import type { ReactNode } from 'react';

import { AuthContext, type AuthContextValue } from '@/auth/auth-context';

export function AuthProvider({ children }: {children: ReactNode}){
    const [token, setToken] = useState<string | null>(null);
    const [ticket, setTicket] = useState<string | null>(null);

    const value: AuthContextValue = {
        token,
        ticket,
        login: (token, ticket) => { setToken(token); setTicket(ticket); },
        logout: () => { setToken(null); setTicket(null); }
    };
   
    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
