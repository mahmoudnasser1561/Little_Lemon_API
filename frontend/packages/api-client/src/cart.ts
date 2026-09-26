import { request } from './http';

export interface CartLine {
  menuitem: number;
  title: string;
  unit_price: string;
  quantity: number;
  price: string;
}

export interface Cart {
  items: CartLine[];
  total: string;
}

export const cart = {
  get(): Promise<Cart> {
    return request('/api/cart/menu-items');
  },
  add(menuitem: number, quantity: number): Promise<CartLine> {
    return request('/api/cart/menu-items', {
      method: 'POST',
      body: JSON.stringify({ menuitem, quantity }),
    });
  },
  updateQuantity(menuitemId: number, quantity: number): Promise<CartLine> {
    return request(`/api/cart/menu-items/${menuitemId}`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    });
  },
  removeLine(menuitemId: number): Promise<void> {
    return request(`/api/cart/menu-items/${menuitemId}`, { method: 'DELETE' });
  },
  clear(): Promise<void> {
    return request('/api/cart/menu-items', { method: 'DELETE' });
  },
};
