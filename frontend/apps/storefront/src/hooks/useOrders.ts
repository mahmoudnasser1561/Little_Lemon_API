import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { orders, getToken } from '@little-lemon/api-client';

export function useOrders(page?: number) {
  return useQuery({
    queryKey: ['orders', page ?? 1],
    queryFn: () => orders.list(page),
    enabled: Boolean(getToken()),
  });
}

export function useOrder(id: number) {
  return useQuery({
    queryKey: ['order', id],
    queryFn: () => orders.get(id),
    enabled: Boolean(getToken()) && Number.isFinite(id),
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => orders.create(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['cart'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}
