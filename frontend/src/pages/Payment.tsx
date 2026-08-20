import { useState, type SubmitEvent } from "react";
import { useNavigate } from "react-router-dom";

import { apiPost } from "../api/client";

export default function Payment() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [expiration, setExpiration] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const submit = async (event: SubmitEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const confirmation = await apiPost<{ order_id: number; items: unknown[]; total: number }>(
        "/checkout",
        { first_name: firstName, last_name: lastName, card_number: cardNumber, expiration },
      );
      navigate(`/confirmation/${confirmation.order_id}`, { state: confirmation });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    }
  };

  return (
    <form onSubmit={submit}>
      <h1>Payment</h1>
      <label>
        First name
        <input
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          autoComplete="cc-given-name"
          required
        />
      </label>
      <label>
        Last name
        <input
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          autoComplete="cc-family-name"
          required
        />
      </label>
      <label>
        Card number
        <input
          value={cardNumber}
          onChange={(e) => setCardNumber(e.target.value)}
          placeholder="1234 5678 9012 3456"
          inputMode="numeric"
          autoComplete="cc-number"
          required
        />
      </label>
      <label>
        Expiration date
        <input
          type="date"
          value={expiration}
          onChange={(e) => setExpiration(e.target.value)}
          required
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit">Place Order</button>
    </form>
  );
}