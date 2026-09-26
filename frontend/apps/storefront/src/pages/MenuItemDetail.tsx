import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getToken, menu as menuApi } from '@little-lemon/api-client';
import { Badge, Button, Stepper } from '@little-lemon/ui';
import { BackIcon, DishIcon } from '../components/icons';
import { useAddToCart } from '../hooks/useCart';

export function MenuItemDetail() {
  const { id } = useParams<{ id: string }>();
  const itemId = Number(id);
  const [quantity, setQuantity] = useState(1);
  const navigate = useNavigate();
  const addToCart = useAddToCart();

  const itemQuery = useQuery({
    queryKey: ['menu-item', itemId],
    queryFn: () => menuApi.get(itemId),
    enabled: Number.isFinite(itemId),
  });

  function handleAddToCart() {
    if (!getToken()) {
      navigate('/login', { state: { from: { pathname: `/menu/${itemId}` } } });
      return;
    }
    addToCart.mutate({ menuitem: itemId, quantity });
  }

  return (
    <div className="flex-grow">
      <div className="px-12 pt-7">
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-text-secondary hover:text-text">
          <BackIcon /> Back to menu
        </Link>
      </div>

      {itemQuery.isLoading && <p className="px-12 pt-8 text-text-secondary">Loading…</p>}
      {itemQuery.isError && <p className="px-12 pt-8 text-danger">Couldn't load this dish. Is the API running?</p>}

      {itemQuery.data && (
        <div className="px-12 pt-6 pb-16 grid grid-cols-[560px_1fr] gap-16 max-w-[1344px]">
          <div className="h-[420px] rounded-lg bg-accent-soft text-accent flex items-center justify-center overflow-hidden">
            {itemQuery.data.image ? (
              <img src={itemQuery.data.image} alt={itemQuery.data.title} className="w-full h-full object-cover" />
            ) : (
              <DishIcon size={64} />
            )}
          </div>
          <div className="flex flex-col gap-5 pt-2">
            {itemQuery.data.featured && (
              <Badge tone="accent" className="self-start">
                Featured
              </Badge>
            )}
            <div>
              <h1 className="font-display text-[36px]">{itemQuery.data.title}</h1>
              <p className="text-text-secondary mt-2">{itemQuery.data.category.title}</p>
            </div>
            <div className="font-semibold tabular-nums text-[32px]">${itemQuery.data.price}</div>
            <div className="h-px bg-border" />
            <div className="flex flex-col gap-1.5 max-w-[200px]">
              <span className="text-sm font-semibold">Quantity</span>
              <Stepper value={quantity} onChange={setQuantity} />
            </div>
            <Button className="w-[260px] mt-1" onClick={handleAddToCart} disabled={addToCart.isPending}>
              {addToCart.isPending ? 'Adding…' : `Add to cart — $${(Number(itemQuery.data.price) * quantity).toFixed(2)}`}
            </Button>
            {addToCart.isSuccess && <p className="text-sm text-olive font-medium">Added to cart.</p>}
            {addToCart.isError && <p className="text-sm text-danger font-medium">Couldn't add this to your cart.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
