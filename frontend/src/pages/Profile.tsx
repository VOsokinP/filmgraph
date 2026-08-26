import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { apiGet, errorMessage, isAuthRedirect } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import { CartIcon } from '../components/ui/Icons';

interface OrderLine {
    movie_id: string;
    title: string;
    quantity: number;
    price: number;
}
interface Order {
    id: number;
    orderDate: string;
    total: number;
    items: OrderLine[];
}

function formatOrderDate(isoDate: string): string {
    const asLocalMidnight = new Date(`${isoDate}T00:00:00`);
    if (Number.isNaN(asLocalMidnight.getTime())) return isoDate;
    return asLocalMidnight.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

export default function Profile() {
    const { customer } = useAuth();
    const [orders, setOrders] = useState<Order[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(() => {
        let cancelled = false;
        setError(null);
        setOrders(null);
        apiGet<Order[]>('/orders')
            .then((result) => {
                if (!cancelled) setOrders(result);
            })
            .catch((err) => {
                if (!cancelled && !isAuthRedirect(err)) setError(errorMessage(err));
            });
        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(load, [load]);

    if (error) {
        return <ErrorState message={error} title="Couldn't load your orders" onRetry={load} />;
    }

    return (
        <>
            <div className="page-head">
                <div>
                    <h1>{customer ? `${customer.firstName} ${customer.lastName}` : 'Profile'}</h1>
                    {customer && <p className="detail__subtitle">{customer.email}</p>}
                </div>
                {orders && (
                    <p className="page-head__meta">
                        {orders.length} {orders.length === 1 ? 'order' : 'orders'}
                    </p>
                )}
            </div>

            {!orders ? (
                <div className="stack-sm" aria-busy="true">
                    <span className="skeleton" style={{ width: '100%', height: '5em' }} />
                    <span className="skeleton" style={{ width: '100%', height: '5em' }} />
                </div>
            ) : orders.length === 0 ? (
                <div className="panel">
                    <EmptyState
                        icon={<CartIcon size={32} />}
                        title="No orders yet"
                        body="Anything you buy will show up here."
                    />
                </div>
            ) : (
                <div className="stack-sm">
                    {orders.map((order) => (
                        <section className="panel order" key={order.id}>
                            <ul className="order__items">
                                {order.items.map((item) => (
                                    <li key={item.movie_id}>
                                        <Link className="order__title" to={`/movies/${item.movie_id}`}>
                                            {item.title}
                                        </Link>
                                        <span className="order__qty">
                                            {item.quantity} x ${item.price.toFixed(2)}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                            <div className="order__foot">
                                <span className="order__date">
                                    {formatOrderDate(order.orderDate)}
                                </span>
                                <span className="order__total">${order.total.toFixed(2)}</span>
                            </div>
                        </section>
                    ))}
                </div>
            )}
        </>
    );
}
