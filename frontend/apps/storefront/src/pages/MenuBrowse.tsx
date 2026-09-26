import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { categories as categoriesApi, menu as menuApi } from '@little-lemon/api-client';
import type { MenuListParams } from '@little-lemon/api-client';
import { Badge, Card, Chip, Pagination } from '@little-lemon/ui';
import { DishIcon } from '../components/icons';

type Ordering = MenuListParams['ordering'];

export function MenuBrowse() {
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<string | null>(null);
  const [ordering, setOrdering] = useState<Ordering>(undefined);

  // search_fields on the API is ['category__title'] only (B25, still open) - passing a
  // category's own title as `search` is a real, working filter-by-category, not a
  // client-side simulation. There's no dish-name search until that bug is fixed.
  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.listAll(),
  });

  const menuQuery = useQuery({
    queryKey: ['menu', page, category, ordering],
    queryFn: () => menuApi.list({ page, search: category ?? undefined, ordering }),
  });

  function selectCategory(title: string | null) {
    setCategory(title);
    setPage(1);
  }

  return (
    <div className="flex-grow">
      <div className="px-12 pt-12 pb-6">
        <h1 className="font-display text-[40px]">Our menu</h1>
        <p className="text-text-secondary mt-1.5">Char-grilled and fresh Mediterranean dishes, made to order.</p>
      </div>

      <div className="px-12 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex gap-2.5 flex-wrap">
          <Chip active={category === null} onClick={() => selectCategory(null)}>
            All
          </Chip>
          {categoriesQuery.data?.map((c) => (
            <Chip key={c.id} active={category === c.title} onClick={() => selectCategory(c.title)}>
              {c.title}
            </Chip>
          ))}
        </div>
        <select
          aria-label="Sort by price"
          className="h-11 px-3.5 rounded-sm border border-border-strong bg-white text-sm"
          value={ordering ?? ''}
          onChange={(e) => {
            setOrdering((e.target.value || undefined) as Ordering);
            setPage(1);
          }}
        >
          <option value="">Default order</option>
          <option value="price">Price: Low to high</option>
          <option value="-price">Price: High to low</option>
        </select>
      </div>

      <div className="px-12 pt-6 pb-16">
        {menuQuery.isLoading && <p className="text-text-secondary">Loading…</p>}
        {menuQuery.isError && <p className="text-danger">Couldn't load the menu right now. Is the API running?</p>}
        {menuQuery.data && menuQuery.data.results.length === 0 && (
          <p className="text-text-secondary">No dishes match this filter.</p>
        )}

        {menuQuery.data && menuQuery.data.results.length > 0 && (
          <div className="grid grid-cols-3 gap-6">
            {menuQuery.data.results.map((item) => (
              <Link key={item.id} to={`/menu/${item.id}`}>
                <Card className="flex flex-col overflow-hidden h-full">
                  <div className="h-40 bg-accent-soft text-accent flex items-center justify-center relative overflow-hidden">
                    {item.image ? (
                      <img src={item.image} alt={item.title} loading="lazy" className="w-full h-full object-cover" />
                    ) : (
                      <DishIcon />
                    )}
                    {item.featured && (
                      <Badge tone="accent" className="absolute top-3 left-3">
                        Featured
                      </Badge>
                    )}
                  </div>
                  <div className="p-4 flex flex-col gap-2 flex-grow">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-display text-[17px] leading-snug">{item.title}</h3>
                      <span className="font-semibold tabular-nums text-[15px]">${item.price}</span>
                    </div>
                    <Badge tone="neutral" className="self-start mt-auto">
                      {item.category.title}
                    </Badge>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}

        {menuQuery.data && (
          <div className="mt-8">
            <Pagination
              page={page}
              hasPrevious={Boolean(menuQuery.data.previous)}
              hasNext={Boolean(menuQuery.data.next)}
              onPrevious={() => setPage((p) => Math.max(1, p - 1))}
              onNext={() => setPage((p) => p + 1)}
              totalCount={menuQuery.data.count}
            />
          </div>
        )}
      </div>
    </div>
  );
}
