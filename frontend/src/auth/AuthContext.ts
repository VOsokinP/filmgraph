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
    refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthState>({
    customer: null,
    loading: true,
    refresh: async () => {},
});

export const useAuth = () => useContext(AuthContext);
