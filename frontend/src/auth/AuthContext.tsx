import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

export interface AuthContextValue {
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

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

export function useAuth(){
    const context = useContext(AuthContext);
    if(!context){
        throw new Error("useAuth must be used within AuthProvider");
    }
    return context;
}