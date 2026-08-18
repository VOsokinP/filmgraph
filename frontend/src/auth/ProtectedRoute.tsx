import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./AuthContext";

export default function ProtectedRoute() {
    const { customer, loading } = useAuth();
    if (loading) return <p>Loading...</p>;
    return customer ? <Outlet /> : <Navigate to="/login" replace />;
}