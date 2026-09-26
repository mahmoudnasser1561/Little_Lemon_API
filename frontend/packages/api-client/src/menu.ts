import { request } from './http';
import type { MenuItem, MenuListParams, Paginated } from './types';

export interface MenuItemPayload {
  title: string;
  price: string;
  featured: boolean;
  category_id: number;
  image?: File | null;
}

function buildQuery(params: MenuListParams): string {
  const qs = new URLSearchParams();
  if (params.page) qs.set('page', String(params.page));
  if (params.search) qs.set('search', params.search);
  if (params.ordering) qs.set('ordering', params.ordering);
  const s = qs.toString();
  return s ? `?${s}` : '';
}

function toFormData(payload: MenuItemPayload): FormData {
  const form = new FormData();
  form.set('title', payload.title);
  form.set('price', payload.price);
  form.set('featured', String(payload.featured));
  form.set('category_id', String(payload.category_id));
  if (payload.image) form.set('image', payload.image);
  return form;
}

export const menu = {
  /** GET /api/menu-items/ - trailing slash required, this is the list route. */
  list(params: MenuListParams = {}): Promise<Paginated<MenuItem>> {
    return request(`/api/menu-items/${buildQuery(params)}`);
  },
  /** GET /api/menu-items/<id> - no trailing slash: the detail route is a distinct URL
   * pattern on the API (restaurant/urls.py), not the list route with an id appended. */
  get(id: number): Promise<MenuItem> {
    return request(`/api/menu-items/${id}`);
  },
  create(payload: MenuItemPayload): Promise<MenuItem> {
    return request('/api/menu-items/', { method: 'POST', body: toFormData(payload) });
  },
  update(id: number, payload: MenuItemPayload): Promise<MenuItem> {
    return request(`/api/menu-items/${id}`, { method: 'PATCH', body: toFormData(payload) });
  },
  remove(id: number): Promise<void> {
    return request(`/api/menu-items/${id}`, { method: 'DELETE' });
  },
};
