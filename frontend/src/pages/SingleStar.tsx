import { useEffect, useState } from 'react';
import { Link, useParams, useLocation } from 'react-router-dom';

import { apiGet } from '../api/client';

interface StarDetail {
    id: string;
    name: string;
    birth_year: number | null;
    movies: {id: string; title: string}[];
}

export default function SingleStar() {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const backTo = (location.state as { from?: string }).from ?? "/";
    const [star, setStar] = useState<StarDetail | null>(null);

    useEffect(() => {
        apiGet<StarDetail>(`/stars/${id}`).then(setStar);
    }, [id]);

    if (!star) return <p>Loading...</p>;

    return (
        <div>
            <h1>{star.name}</h1>
            <p> Born: {star.birth_year ?? 'N/A'}</p>
            <ul>
                {star.movies.map((m) => (
                    <li key={m.id}>
                        <Link to={`/movies/${m.id}`} state={{ from: backTo }}>{m.title}</Link>
                    </li>
                ))}
            </ul>
            <Link to={backTo}>Back to Movie List</Link>
        </div>
    );
}