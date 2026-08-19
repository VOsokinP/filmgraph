import { useState } from "react";

import { apiPost } from "../api/client";

export default function AddToCartButton({ movieId }: { movieId: string }) {
    const [message, setMessage] = useState<string | null>(null);

    const handleClick = async () => {
        try {
            await apiPost("/cart/items", { movie_id: movieId, delta: 1 });
            setMessage("Added!");
        } catch {
            setMessage("Failed to add");
        }
    };

    return (
        <span>
            <button onClick={handleClick}>Add to Cart</button>
            {message && <span> {message}</span>}
        </span>
    );
}