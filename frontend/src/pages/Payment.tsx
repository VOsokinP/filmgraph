import { useEffect, useState, type SubmitEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { apiGet, apiPost } from "../api/client";
import { useCartCount } from "../cart/CartCountContext";
import Button from "../components/ui/Button";
import Field from "../components/ui/Field";
import { AlertIcon, ChevronLeftIcon } from "../components/ui/Icons";

interface DemoCard {
  id: string;
  firstName: string;
  lastName: string;
  expiration: string;
}

export default function Payment() {
  const [card, setCard] = useState<DemoCard | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [expiration, setExpiration] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const { refreshCount } = useCartCount();
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    apiGet<DemoCard>("/cards/me")
      .then((issued) => {
        if (cancelled) return;
        setCard(issued);
        setFirstName(issued.firstName);
        setLastName(issued.lastName);
        setCardNumber(issued.id);
        setExpiration(issued.expiration);
      })
      .catch(() => {
        if (!cancelled) setCard(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const submit = async (event: SubmitEvent) => {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const confirmation = await apiPost<{ order_id: number; items: unknown[]; total: number }>(
        "/checkout",
        { first_name: firstName, last_name: lastName, card_number: cardNumber, expiration },
      );
      await refreshCount();
      navigate(`/confirmation/${confirmation.order_id}`, { state: confirmation });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    } finally {
      setPending(false);
    }
  };

  return (
    <>
      <Link to="/cart" className="back-link">
        <ChevronLeftIcon size={15} />
        Back to cart
      </Link>

      <div className="narrow">
        <div className="page-head">
          <h1>Payment</h1>
        </div>

        <form className="card form" onSubmit={submit}>
          <fieldset>
            <legend>Cardholder</legend>
            <div className="form__row">
              <Field
                label="First name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                autoComplete="cc-given-name"
                readOnly={card !== null}
                required
              />
              <Field
                label="Last name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                autoComplete="cc-family-name"
                readOnly={card !== null}
                required
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Card details</legend>
            <div className="form__row">
              <Field
                label="Card number"
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
                placeholder="1234 5678 9012 3456"
                inputMode="numeric"
                autoComplete="cc-number"
                readOnly={card !== null}
                hint={card ? "Demo card issued with your account" : undefined}
                required
              />
              <Field
                label="Expiration date"
                type="date"
                value={expiration}
                onChange={(e) => setExpiration(e.target.value)}
                autoComplete="cc-exp"
                readOnly={card !== null}
                required
              />
            </div>
          </fieldset>

          {error && (
            <p className="alert alert--error" role="alert">
              <AlertIcon size={16} className="alert__icon" />
              {error}
            </p>
          )}

          <Button type="submit" variant="primary" block pending={pending}>
            Place order
          </Button>
          <p className="buybox__note">
            {card
              ? "Mock checkout. These are the demo card details issued with your account, and no real payment is processed."
              : "Mock checkout. Card details are validated against seeded test data, and no real payment is processed."}
          </p>
        </form>
      </div>
    </>
  );
}
