import { request } from './http';
import type { Category, Paginated } from './types';

export interface CategoryPayload {
  slug: string;
  title: string;
}

function list(page?: number): Promise<Paginated<Category>> {
  const qs = page ? `?page=${page}` : '';
  return request(`/api/categories/${qs}`);
}

function create(payload: CategoryPayload): Promise<Category> {
  return request('/api/categories/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** Walks every page and returns the full, unpaginated list - for UI (like the menu's
 * category-filter chips) that genuinely needs the complete set, not one paginated
 * slice. Categories are a small, rarely-changing list, so this is fine here; the same
 * pattern would be wrong for menu.list, which can be arbitrarily large.
 *
 * Pages by number (1, 2, 3, ...), not by following the API's `next` field: `next` is an
 * absolute URL built from the backend's own host, and fetching it directly from the
 * browser would bypass the dev proxy (and later, the ingress) and hit the API's origin
 * directly - which has no CORS headers configured. */
async function listAll(): Promise<Category[]> {
  const all: Category[] = [];
  let page = 1;
  for (;;) {
    const response = await list(page);
    all.push(...response.results);
    if (!response.next) break;
    page += 1;
  }
  return all;
}

export const categories = { list, listAll, create };
