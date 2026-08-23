interface RegisterResponseSuccess{
    success: string;
    token: string;
}

interface RegisterResponseError{
    error: string;
}

export type RegisterResponse = RegisterResponseSuccess | RegisterResponseError;

export interface LoginResponse{
    token: string;
}