import { useState } from 'react';
import type { ReactNode } from 'react';

import { AuthContext, type AuthContextValue } from '@/auth/auth-context';

export function AuthProvider({ children }: {children: ReactNode}){
    const [token, setToken] = useState<string | null>(null);

    const value: AuthContextValue = {
        token,
        login: (t) => setToken(t),
        logout: () => setToken(null)
    };
   
    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
