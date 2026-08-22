import { useEffect, useState, type ReactNode } from 'react';

import { apiGet } from '../api/client';
import { AuthContext, type Customer } from './AuthContext';

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
