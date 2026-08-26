import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { apiGet, errorMessage, isAuthRedirect } from "../api/client";
import ErrorState from "../components/ui/ErrorState";
import { CheckIcon } from "../components/ui/Icons";

interface SaleLine {
  movie_id: string;
  title: string;
  quantity: number;
  price: number;
}
interface Order {
  id: number;
  orderDate: string;
  total: number;
  items: SaleLine[];
}

export default function Confirmation() {
  const { orderId } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setError(null);
    setOrder(null);
    apiGet<Order>(`/orders/${orderId}`)
      .then((result) => {
        if (!cancelled) setOrder(result);
      })
      .catch((err) => {
        if (!cancelled && !isAuthRedirect(err)) setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  useEffect(load, [load]);

  if (error) {
    return <ErrorState message={error} title="Couldn't load this order" onRetry={load} />;
  }

  if (!order) {
    return (
      <div className="narrow stack-sm" aria-busy="true">
        <span className="skeleton" style={{ width: "60%", height: "2em" }} />
        <span className="skeleton" style={{ width: "100%", height: "6em" }} />
      </div>
    );
  }

  return (
    <div className="narrow">
      <div className="confirm-head">
        <span className="confirm-head__icon">
          <CheckIcon size={26} />
        </span>
        <h1>Order confirmed</h1>
        <p className="confirm-head__order">Order #{order.id}</p>
      </div>

      <div className="table-wrap">
        <table className="table">
          <caption className="visually-hidden">Items in order {order.id}</caption>
          <thead>
            <tr>
              <th scope="col">
                <span className="th-label">Title</span>
              </th>
              <th scope="col" className="num">
                <span className="th-label">Qty</span>
              </th>
              <th scope="col" className="num">
                <span className="th-label">Price</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item) => (
              <tr key={item.movie_id}>
                <td>
                  <Link className="title-cell" to={`/movies/${item.movie_id}`}>
                    {item.title}
                  </Link>
                </td>
                <td className="num">{item.quantity}</td>
                <td className="num">${item.price.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel summary" style={{ marginTop: 'var(--space-5)' }}>
        <div className="summary__row summary__row--total">
          <span>Total</span>
          <span className="summary__amount summary__amount--total">
            ${order.total.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="confirm-actions">
        <Link to="/profile" className="btn btn--secondary">
          View all orders
        </Link>
        <Link to="/" className="btn btn--primary">
          Back to movie list
        </Link>
      </div>
    </div>
  );
}
