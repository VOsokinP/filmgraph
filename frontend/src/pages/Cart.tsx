import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { apiDelete, apiGet, apiPost, errorMessage, isAuthRedirect } from "../api/client";
import { useCartCount } from "../cart/CartCountContext";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import { AlertIcon, CartIcon, ChevronLeftIcon, MinusIcon, PlusIcon } from "../components/ui/Icons";

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
    const [loadError, setLoadError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const { refreshCount } = useCartCount();
    const navigate = useNavigate();

    const load = useCallback(async () => {
        setLoadError(null);
        try {
            setCart(await apiGet<CartOut>("/cart"));
        } catch (err) {
            if (!isAuthRedirect(err)) setLoadError(errorMessage(err));
        }
    }, []);

    const reload = useCallback(() => {
        setCart(null);
        void load();
    }, [load]);

    useEffect(() => {
        void load();
    }, [load]);

    const mutate = async (action: () => Promise<unknown>) => {
        setBusy(true);
        setActionError(null);
        try {
            await action();
            await load();
            await refreshCount();
        } catch (err) {
            if (!isAuthRedirect(err)) setActionError(errorMessage(err));
        } finally {
            setBusy(false);
        }
    };

    const changeQty = (movieId: string, delta: number) =>
        mutate(() => apiPost("/cart/items", { movie_id: movieId, delta }));

    const removeItem = (movieId: string) => mutate(() => apiDelete(`/cart/items/${movieId}`));

    if (loadError) {
        return <ErrorState message={loadError} title="Couldn't load your cart" onRetry={reload} />;
    }

    if (!cart) {
        return (
            <div className="stack-sm" aria-busy="true">
                <span className="skeleton" style={{ width: "30%", height: "2em" }} />
                <span className="skeleton" style={{ width: "100%", height: "6em" }} />
            </div>
        );
    }

    const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);

    return (
        <>
            <Link to="/" className="back-link">
                <ChevronLeftIcon size={15} />
                Back to movie list
            </Link>

            <div className="page-head">
                <h1>Shopping cart</h1>
                {itemCount > 0 && (
                    <p className="page-head__meta">
                        {itemCount} {itemCount === 1 ? "item" : "items"}
                    </p>
                )}
            </div>

            {actionError && (
                <p className="alert alert--error" role="alert">
                    <AlertIcon size={16} className="alert__icon" />
                    {actionError}
                </p>
            )}

            {cart.items.length === 0 ? (
                <div className="panel">
                    <EmptyState
                        icon={<CartIcon size={32} />}
                        title="Your cart is empty"
                        body="Browse the catalog and add a few titles to get started."
                        action={
                            <Button variant="primary" onClick={() => navigate("/")}>
                                Browse movies
                            </Button>
                        }
                    />
                </div>
            ) : (
                <div className="checkout">
                    <div className="table-wrap">
                        <table className="table">
                            <caption className="visually-hidden">Items in your cart</caption>
                            <thead>
                                <tr>
                                    <th scope="col">
                                        <span className="th-label">Title</span>
                                    </th>
                                    <th scope="col" className="num">
                                        <span className="th-label">Price</span>
                                    </th>
                                    <th scope="col">
                                        <span className="th-label">Quantity</span>
                                    </th>
                                    <th scope="col" className="num">
                                        <span className="th-label">Subtotal</span>
                                    </th>
                                    <th scope="col" className="shrink">
                                        <span className="visually-hidden">Actions</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {cart.items.map((item) => (
                                    <tr key={item.movie_id}>
                                        <td>
                                            <Link className="title-cell" to={`/movies/${item.movie_id}`}>
                                                {item.title}
                                            </Link>
                                        </td>
                                        <td className="num">${item.price.toFixed(2)}</td>
                                        <td>
                                            <span className="qty">
                                                <button
                                                    type="button"
                                                    className="qty__btn"
                                                    onClick={() => changeQty(item.movie_id, -1)}
                                                    disabled={busy}
                                                    aria-label={`Decrease quantity of ${item.title}`}
                                                >
                                                    <MinusIcon size={14} />
                                                </button>
                                                <span className="qty__value">{item.quantity}</span>
                                                <button
                                                    type="button"
                                                    className="qty__btn"
                                                    onClick={() => changeQty(item.movie_id, 1)}
                                                    disabled={busy}
                                                    aria-label={`Increase quantity of ${item.title}`}
                                                >
                                                    <PlusIcon size={14} />
                                                </button>
                                            </span>
                                        </td>
                                        <td className="num">${item.subtotal.toFixed(2)}</td>
                                        <td className="shrink">
                                            <Button
                                                variant="danger"
                                                size="sm"
                                                onClick={() => removeItem(item.movie_id)}
                                                disabled={busy}
                                                aria-label={`Remove ${item.title} from cart`}
                                            >
                                                Remove
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <aside className="panel summary">
                        <h2>Order summary</h2>
                        <div className="summary__row">
                            <span>
                                Subtotal ({itemCount} {itemCount === 1 ? "item" : "items"})
                            </span>
                            <span className="summary__amount">${cart.total.toFixed(2)}</span>
                        </div>
                        <div className="summary__row summary__row--total">
                            <span>Total</span>
                            <span className="summary__amount summary__amount--total">
                                ${cart.total.toFixed(2)}
                            </span>
                        </div>
                        <Button
                            variant="primary"
                            block
                            disabled={busy}
                            onClick={() => navigate("/payment")}
                        >
                            Proceed to payment
                        </Button>
                    </aside>
                </div>
            )}
        </>
    );
}
