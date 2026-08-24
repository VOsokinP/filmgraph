import { createContext, useContext } from 'react';

export interface Customer {
    id: number;
    firstName: string;
    lastName: string;
    email: string;
}

export interface AuthState {
    customer: Customer | null;
    loading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthState>({
    customer: null,
    loading: true,
    error: null,
    refresh: async () => {},
});

export const useAuth = () => useContext(AuthContext);
