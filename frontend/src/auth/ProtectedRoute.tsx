import { Navigate, Outlet, useLocation } from "react-router-dom";

import ErrorState from "../components/ui/ErrorState";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute() {
    const { customer, loading, error, refresh } = useAuth();
    const location = useLocation();

    if (loading) return <p>Loading...</p>;

    if (error) {
        return (
            <div className="page">
                <ErrorState
                    message={error}
                    title="Couldn't reach FilmGraph"
                    onRetry={() => {
                        void refresh();
                    }}
                />
            </div>
        );
    }

    if (customer) return <Outlet />;

    return (
        <Navigate
            to="/login"
            replace
            state={{ from: `${location.pathname}${location.search}` }}
        />
    );
}