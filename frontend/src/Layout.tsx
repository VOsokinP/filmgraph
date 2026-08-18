import { Link, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import { apiPost } from "./api/client";

export default function Layout() {
  const { refresh } = useAuth();
  const navigate = useNavigate();

  const logout = async () => {
    await apiPost("/auth/logout");
    await refresh();
    navigate("/login");
  };

    return (
        <div>
            <nav>
                <Link to="/">Movies</Link>
                <button onClick={logout}>Logout</button>
            </nav>
            <Outlet />
        </div>
    );
}