import { useEffect, useState, type ReactNode } from 'react';

import { ApiError, apiGet, errorMessage } from '../api/client';
import { AuthContext, type Customer } from './AuthContext';

export function AuthProvider({ children }: { children: ReactNode }) {
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = async () => {
        setLoading(true);
        setError(null);
        try {
            setCustomer(await apiGet<Customer>('/auth/me', { redirectOn401: false }));
        } catch (err) {
            setCustomer(null);
            if (!(err instanceof ApiError && err.status === 401)) setError(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
    }, []);

    return (
        <AuthContext.Provider value={{ customer, loading, error, refresh }}>{children}</AuthContext.Provider>
    );
}
