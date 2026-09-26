/**
 * Shapes match the DRF serializers exactly (see restaurant/serializers.py) - including
 * their quirks, documented inline rather than papered over, so later phases don't get
 * surprised by them.
 */

/** DRF's PageNumberPagination envelope. Default PAGE_SIZE=12, client-adjustable via
 * ?page_size= (capped at 50, see restaurant/pagination.py) - pagination UI is still
 * never optional, just less painful than the original PAGE_SIZE=2. `next`/`previous`
 * are full URLs, not page numbers. */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Category {
  id: number;
  slug: string;
  title: string;
}

export interface MenuItem {
  id: number;
  title: string;
  price: string; // DRF serializes DecimalField as a string, e.g. "12.50" - never parse to float for money math
  featured: boolean;
  category: Category;
  /** Relative (/media/...) under local storage, or a directly-reachable URL once
   * S3/MinIO is active - either way, use it as-is in an <img src>. null when the item
   * has no photo; most seeded/demo items won't. */
  image: string | null;
}

/** Manager and delivery_crew only come from group membership; anyone else is a plain
 * customer. See restaurant.serializers.CurrentUserSerializer.get_role. */
export type Role = 'manager' | 'delivery_crew' | 'customer';

/** GET /api/users/me/ - only this endpoint returns `role`; every other user-ish
 * endpoint (Djoser's defaults) does not. */
export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  role: Role;
}

export interface MenuListParams {
  page?: number;
  /** Only matches category__title server-side (B25: dish-name search is a known, still-open
   * gap) - label this control "search by category" in the UI, not "search dishes". */
  search?: string;
  /** Only 'price' is safe. `ordering_fields` on the API also lists 'inventory', which does
   * not exist on the model and 500s if sent (B8, still open) - never offer it as an option. */
  ordering?: 'price' | '-price';
}
