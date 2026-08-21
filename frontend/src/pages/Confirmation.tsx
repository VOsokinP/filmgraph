import { Link, useLocation, useParams } from "react-router-dom";

import { CheckIcon } from "../components/ui/Icons";

interface SaleLine {
  movie_id: string;
  title: string;
  quantity: number;
  price: number;
}
interface ConfirmationState {
  order_id: number;
  items: SaleLine[];
  total: number;
}

export default function Confirmation() {
  const { orderId } = useParams();
  const location = useLocation();
  const confirmation = location.state as ConfirmationState | undefined;

  if (!confirmation) {
    // Direct visit or a refresh — router state doesn't survive either. A future
    // GET /api/orders/{id} endpoint would fix this properly; noted as a follow-up, not built here.
    return (
      <div className="narrow">
        <div className="confirm-head">
          <span className="confirm-head__icon">
            <CheckIcon size={26} />
          </span>
          <h1>Order placed</h1>
          <p className="confirm-head__order">Order #{orderId}</p>
          <p className="muted">Refreshing this page lost the line-item details for this order.</p>
        </div>
        <Link to="/" className="btn btn--primary btn--block">
          Back to movie list
        </Link>
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
        <p className="confirm-head__order">Order #{confirmation.order_id}</p>
      </div>

      <div className="table-wrap">
        <table className="table">
          <caption className="visually-hidden">Items in order {confirmation.order_id}</caption>
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
            {confirmation.items.map((item) => (
              <tr key={item.movie_id}>
                <td>{item.title}</td>
                <td className="num">{item.quantity}</td>
                <td className="num">${item.price.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel summary" style={{ marginTop: 'var(--space-5)' }}>
        <div className="summary__row summary__row--total" style={{ paddingTop: 0, borderTop: 'none' }}>
          <span>Total paid</span>
          <span className="summary__amount summary__amount--total">
            ${confirmation.total.toFixed(2)}
          </span>
        </div>
        <Link to="/" className="btn btn--secondary btn--block">
          Back to movie list
        </Link>
      </div>
    </div>
  );
}
