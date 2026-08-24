import { Navigate, Outlet } from "react-router-dom";

import ErrorState from "../components/ui/ErrorState";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute() {
    const { customer, loading, error, refresh } = useAuth();

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

    return customer ? <Outlet /> : <Navigate to="/login" replace />;
}