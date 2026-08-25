import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from './auth/AuthContext';
import { CartCountProvider } from './cart/CartCountProvider';
import { useCartCount } from './cart/CartCountContext';
import { apiPost } from './api/client';
import Button from './components/ui/Button';
import { CartIcon, FilmIcon, LogOutIcon } from './components/ui/Icons';

function Header() {
  const { customer, loading, refresh } = useAuth();
  const { count } = useCartCount();
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutFailed, setLogoutFailed] = useState(false);
  const navigate = useNavigate();

  const logout = async () => {
    setLoggingOut(true);
    setLogoutFailed(false);
    try {
      await apiPost('/auth/logout');
    } catch {
      setLogoutFailed(true);
      return;
    } finally {
      setLoggingOut(false);
    }
    await refresh();
    navigate('/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'app-nav__link is-active' : 'app-nav__link';

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <Link to="/" className="brand">
          <FilmIcon size={20} className="brand__mark" />
          FilmGraph
        </Link>

        <nav className="app-nav" aria-label="Main">
          <NavLink to="/" end className={navClass}>
            Movies
          </NavLink>
          <NavLink to="/cart" className={navClass}>
            <CartIcon size={16} />
            Cart
            {count > 0 && (
              <span className="badge">
                {count}
                <span className="visually-hidden"> items in cart</span>
              </span>
            )}
          </NavLink>
        </nav>

        <div className="app-header__user">
          {loading ? null : customer ? (
            <>
              <span className="app-header__name">
                {customer.firstName} {customer.lastName}
              </span>
              <Button variant="ghost" size="sm" onClick={logout} pending={loggingOut}>
                <LogOutIcon size={14} />
                Log out
              </Button>
              {logoutFailed && (
                <span className="app-header__logout-error" role="alert">
                  Log out failed, still signed in
                </span>
              )}
            </>
          ) : (
            <Link to="/login" className="btn btn--secondary btn--sm">
              Log in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export default function Layout() {
  return (
    <CartCountProvider>
      <Header />
      <main className="page">
        <Outlet />
      </main>
    </CartCountProvider>
  );
}
