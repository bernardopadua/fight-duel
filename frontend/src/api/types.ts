// Result 
interface RegisterResponseSuccess{
    success: string;
    token: string;
}

interface RegisterResponseError{
    error: string;
}

export type RegisterResponse = RegisterResponseSuccess | RegisterResponseError;

export interface LoginResponse{
    error?: string;
    token: string;
}

// Payloads
export interface PlayerCreationPayload {
    playerName: string;
}