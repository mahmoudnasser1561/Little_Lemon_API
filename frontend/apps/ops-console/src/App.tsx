import { Route, Routes } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { RequireStaffAuth } from './components/RequireStaffAuth';
import { useCurrentUser } from './hooks/useAuth';
import { Login } from './pages/Login';
import { Categories } from './pages/Categories';
import { MenuItems } from './pages/MenuItems';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <RequireStaffAuth>
            <Shell />
          </RequireStaffAuth>
        }
      />
    </Routes>
  );
}

function Shell() {
  const { data: user } = useCurrentUser();
  const isManager = user?.role === 'manager';

  return (
    <div className="min-h-screen flex bg-bg">
      <Sidebar />
      <div className="flex-grow flex flex-col">
        <Routes>
          <Route path="/menu-items" element={isManager ? <MenuItems /> : <NothingHere />} />
          <Route path="/categories" element={isManager ? <Categories /> : <NothingHere />} />
          <Route path="/" element={isManager ? <MenuItems /> : <NothingHere />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </div>
  );
}

function NothingHere() {
  return <div className="flex-grow flex items-center justify-center text-text-secondary">Nothing here for you yet.</div>;
}

function NotFound() {
  return (
    <div className="flex-grow flex items-center justify-center text-text-secondary">
      <p>Page not found.</p>
    </div>
  );
}
