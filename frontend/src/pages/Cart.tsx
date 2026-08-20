import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { apiDelete, apiGet, apiPost } from "../api/client";

interface CartLine {
  movie_id: string;
  title: string;
  price: number;
  quantity: number;
  subtotal: number;
}
interface CartOut {
  items: CartLine[];
  total: number;
}

export default function Cart() {
    const [cart, setCart] = useState<CartOut | null>(null);
    const navigate = useNavigate();

    const load = () => apiGet<CartOut>("/cart").then(setCart);
    useEffect(() => {
        load();
    }, []);

    const changeQty = async (movieId: string, delta: number) => {
        await apiPost("/cart/items", { movie_id: movieId, delta });
        load();
    }

    const removeItem = async (movieId: string) => {
        await apiDelete(`/cart/items/${movieId}`);
        load();
    }

    if (!cart) return <p>Loading...</p>;

    return (
        <div>
            <h1>Shopping Cart</h1>
            {cart.items.length === 0 ? (
                <p>Your cart is empty.</p>
            ) : (
                <table>
                    <tbody>
                        {cart.items.map((item) => (
                            <tr key={item.movie_id}>
                                <td></td>
                                <td>{item.title}</td>
                                <td>${item.price.toFixed(2)}</td>
                                <td>
                                    <button onClick={() => changeQty(item.movie_id, -1)}>-</button>
                                    {item.quantity}
                                    <button onClick={() => changeQty(item.movie_id, 1)}>+</button>
                                </td>
                                <td>${item.subtotal.toFixed(2)}</td>
                                <td>
                                    <button onClick={() => removeItem(item.movie_id)}>Remove</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
            <p>Total: ${cart.total.toFixed(2)}</p>
            <button disabled={cart.items.length === 0} onClick={() => navigate("/payment")}>
                Proceed to Payment
            </button>
            <div>
                <Link to="/">Back to Movie List</Link>
            </div>
        </div>
    );
}