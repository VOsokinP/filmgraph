import { Link, useLocation, useParams } from "react-router-dom";

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
      <div>
        <p>Order #{orderId} was placed. Refreshing lost the details for this view.</p>
        <Link to="/">Back to Movie List</Link>
      </div>
    );
  }

  return (
    <div>
      <h1>Order Confirmed — #{confirmation.order_id}</h1>
      <ul>
        {confirmation.items.map((item) => (
          <li key={item.movie_id}>
            {item.title} × {item.quantity} — ${item.price.toFixed(2)} each
          </li>
        ))}
      </ul>
      <p>Total: ${confirmation.total.toFixed(2)}</p>
      <Link to="/">Back to Movie List</Link>
    </div>
  );
}