import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useCurrentUser, useLogout } from '../hooks/useAuth';

export function RequireStaffAuth({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useCurrentUser();
  const logout = useLogout();
  const location = useLocation();

  if (isLoading) {
    return <div className="flex-grow flex items-center justify-center text-text-secondary">Loading…</div>;
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (user.role === 'customer') {
    return (
      <div className="flex-grow flex items-center justify-center">
        <div className="text-center flex flex-col gap-3 items-center">
          <p className="text-text-secondary">This console is for staff only.</p>
          <button
            type="button"
            onClick={() => logout.mutate()}
            className="text-sm font-semibold text-accent"
          >
            Log out
          </button>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}
