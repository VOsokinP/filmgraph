import { useEffect, useState } from 'react';
import { Link, useParams, useLocation } from 'react-router-dom';

import { apiGet } from '../api/client';

interface StarDetail {
    id: string;
    name: string;
    birth_year: number | null;
    movies: {id: string; title: string; year: number}[];
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
            <h2>Filmography ({star.movies.length})</h2>
            {star.movies.length === 0 ? (
                <p>No movie credits on record.</p>
            ) : (
                <table className="filmography">
                    <thead>
                        <tr>
                            <th scope="col">Title</th>
                            <th scope="col">Year</th>
                        </tr>
                    </thead>
                    <tbody>
                        {star.movies.map((m) => (
                            <tr key={m.id}>
                                <td>
                                    <Link to={`/movies/${m.id}`} state={{ from: backTo }}>{m.title}</Link>
                                </td>
                                <td>{m.year}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
            <Link to={backTo}>Back to Movie List</Link>
        </div>
    );
}