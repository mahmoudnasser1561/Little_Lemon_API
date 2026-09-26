import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useCurrentUser, useLogout } from '../hooks/useAuth';

const ROLE_LABEL: Record<string, string> = {
  manager: 'Manager',
  delivery_crew: 'Delivery crew',
};

const LINKS = [
  { to: '/menu-items', label: 'Menu items', roles: ['manager'] },
  { to: '/categories', label: 'Categories', roles: ['manager'] },
];

export function Sidebar() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const navigate = useNavigate();
  const location = useLocation();

  async function handleLogout() {
    await logout.mutateAsync();
    navigate('/login');
  }

  const links = LINKS.filter((link) => !user || link.roles.includes(user.role));

  return (
    <div className="w-[240px] flex-shrink-0 bg-[#211D17] text-[#EFE9DC] flex flex-col p-4">
      <div className="flex items-center gap-2.5 font-display text-[18px] font-bold text-white px-3 pb-6">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M8 12a4 4 0 0 1 8 0" />
        </svg>
        Little Lemon <span className="opacity-50 font-medium">Ops</span>
      </div>

      <nav className="flex flex-col gap-1">
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className={`h-[42px] px-3 rounded-sm flex items-center text-sm font-semibold ${
              location.pathname === link.to ? 'bg-accent text-white' : 'text-[#C9C0AE] hover:bg-[#332C22] hover:text-white'
            }`}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      {user && (
        <div className="mt-auto flex items-center gap-2.5 pt-3 border-t border-[#3A3227]">
          <div className="w-9 h-9 rounded-full bg-[#3A3227] text-[#EFE9DC] flex items-center justify-center text-[13px] font-bold flex-shrink-0">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <div className="flex-grow min-w-0">
            <div className="text-[13px] font-semibold text-white truncate">{user.username}</div>
            <div className="text-[11px] text-[#A79C87]">{ROLE_LABEL[user.role] ?? user.role}</div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            disabled={logout.isPending}
            aria-label="Log out"
            className="text-[#A79C87] hover:text-white flex-shrink-0"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
