import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

import { apiGet } from '../api/client';

interface CartCountState {
  count: number;
  refreshCount: () => Promise<void>;
}

const CartCountContext = createContext<CartCountState>({
  count: 0,
  refreshCount: async () => {},
});

export function CartCountProvider({ children }: { children: ReactNode }) {
  const [count, setCount] = useState(0);

  const refreshCount = useCallback(async () => {
    try {
      const cart = await apiGet<{ items: { quantity: number }[] }>('/cart');
      setCount(cart.items.reduce((sum, item) => sum + item.quantity, 0));
    } catch {
      setCount(0);
    }
  }, []);

  useEffect(() => {
    refreshCount();
  }, [refreshCount]);

  return (
    <CartCountContext.Provider value={{ count, refreshCount }}>{children}</CartCountContext.Provider>
  );
}

export const useCartCount = () => useContext(CartCountContext);
