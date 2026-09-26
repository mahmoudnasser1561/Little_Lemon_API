import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auth, getToken } from '@little-lemon/api-client';

export function useCurrentUser() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me(),
    enabled: Boolean(getToken()),
    retry: false,
  });
}

export function useStaffLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ username, password }: { username: string; password: string }) => {
      await auth.login(username, password);
      const user = await auth.me();
      if (user.role === 'customer') {
        await auth.logout();
        throw new Error('staff_only');
      }
      return user;
    },
    onSuccess: (user) => {
      queryClient.setQueryData(['me'], user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => auth.logout(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ['me'] });
    },
  });
}
