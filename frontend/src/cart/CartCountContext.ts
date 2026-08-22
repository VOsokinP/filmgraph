import { createContext, useContext } from 'react';

export interface CartCountState {
  count: number;
  refreshCount: () => Promise<void>;
}

export const CartCountContext = createContext<CartCountState>({
  count: 0,
  refreshCount: async () => {},
});

export const useCartCount = () => useContext(CartCountContext);
