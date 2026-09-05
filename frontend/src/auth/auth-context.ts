import { createContext, useContext } from "react";

export interface AuthContextValue {
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(){
    const context = useContext(AuthContext);
    if(!context){
        throw new Error("useAuth must be used within AuthProvider");
    }
    return context;
}