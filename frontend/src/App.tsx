import { BrowserRouter, Routes, Route } from "react-router-dom";

import { AuthProvider } from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";
import Layout from "./Layout";
import Login from "./pages/Login";
import MovieList from "./pages/MovieList";
import NotFound from "./pages/NotFound";
import Register from "./pages/Register";
import SingleMovie from "./pages/SingleMovie";
import SingleStar from "./pages/SingleStar";

import Cart from "./pages/Cart";
import Confirmation from "./pages/Confirmation";
import Payment from "./pages/Payment";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<Layout />}>
            <Route path="/" element={<MovieList />} />
            <Route path="/movies/:id" element={<SingleMovie />} />
            <Route path="/stars/:id" element={<SingleStar />} />
            <Route path="/cart" element={<Cart />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/payment" element={<Payment />} />
              <Route path="/confirmation/:orderId" element={<Confirmation />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
