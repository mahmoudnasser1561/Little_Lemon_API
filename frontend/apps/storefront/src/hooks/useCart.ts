import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { cart, getToken } from '@little-lemon/api-client';

export function useCart() {
  return useQuery({
    queryKey: ['cart'],
    queryFn: () => cart.get(),
    enabled: Boolean(getToken()),
  });
}

export function useAddToCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ menuitem, quantity }: { menuitem: number; quantity: number }) => cart.add(menuitem, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}

export function useUpdateCartQuantity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ menuitemId, quantity }: { menuitemId: number; quantity: number }) => cart.updateQuantity(menuitemId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}

export function useRemoveCartLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (menuitemId: number) => cart.removeLine(menuitemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}

export function useClearCart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cart.clear(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
}
