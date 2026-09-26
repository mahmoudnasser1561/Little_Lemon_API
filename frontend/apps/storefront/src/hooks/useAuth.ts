import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auth, getToken, type ProfileUpdate, type SetPasswordPayload, type SignupPayload } from '@little-lemon/api-client';

/** The presence of a token IS "logged in" for query-enabling purposes; who that token
 * belongs to (username, role) is server state, so it's a query, not local state. */
export function useCurrentUser() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me(),
    enabled: Boolean(getToken()),
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) => auth.login(username, password),
    onSuccess: () => {
      queryClient.refetchQueries({ queryKey: ['me'] });
    },
  });
}

export function useSignup() {
  const login = useLogin();
  return useMutation({
    mutationFn: async (payload: SignupPayload) => {
      await auth.signup(payload);
      await login.mutateAsync({ username: payload.username, password: payload.password });
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

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileUpdate) => auth.updateProfile(data),
    onSuccess: (user) => {
      queryClient.setQueryData(['me'], user);
    },
  });
}

export function useSetPassword() {
  return useMutation({
    mutationFn: (payload: SetPasswordPayload) => auth.setPassword(payload),
  });
}
