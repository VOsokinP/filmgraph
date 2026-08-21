import { useEffect, useRef, useState } from "react";

import { apiPost } from "../api/client";
import { useCartCount } from "../cart/CartCountContext";
import Button from "./ui/Button";
import { CartIcon, CheckIcon } from "./ui/Icons";

type Status = "idle" | "added" | "error";

interface Props {
    movieId: string;
    variant?: "primary" | "secondary";
    size?: "sm" | "md";
}

export default function AddToCartButton({ movieId, variant = "secondary", size = "sm" }: Props) {
    const [status, setStatus] = useState<Status>("idle");
    const [pending, setPending] = useState(false);
    const { refreshCount } = useCartCount();
    const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

    useEffect(() => () => clearTimeout(timer.current), []);

    const handleClick = async () => {
        setPending(true);
        clearTimeout(timer.current);
        try {
            await apiPost("/cart/items", { movie_id: movieId, delta: 1 });
            await refreshCount();
            setStatus("added");
        } catch {
            setStatus("error");
        } finally {
            setPending(false);
            timer.current = setTimeout(() => setStatus("idle"), 3000);
        }
    };

    return (
        <span className="add-cart">
            <Button
                variant={variant}
                size={size}
                onClick={handleClick}
                pending={pending}
                aria-label="Add to cart"
            >
                {!pending && <CartIcon size={size === "sm" ? 13 : 15} />}
                Add
            </Button>
            <span className="add-cart__slot" aria-live="polite">
                {status === "added" && (
                    <span className="cart-feedback">
                        <CheckIcon size={12} />
                        Added
                    </span>
                )}
                {status === "error" && (
                    <span className="cart-feedback cart-feedback--error">Failed</span>
                )}
            </span>
        </span>
    );
}
