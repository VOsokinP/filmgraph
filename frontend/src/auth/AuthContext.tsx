import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

import { apiGet } from '../api/client';

interface Customer {
    id: number;
    firstName: string;
    lastName: string;
    email: string;
}

interface AuthState {
    customer: Customer | null;
    loading: boolean;
    refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
    customer: null,
    loading: true,
    refresh: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [loading, setLoading] = useState(true);

    const refresh = async () => {
        try {
            setCustomer(await apiGet<Customer>('/auth/me'));
        } catch {
            setCustomer(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
    }, []);

    return <AuthContext.Provider value={{ customer, loading, refresh }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);