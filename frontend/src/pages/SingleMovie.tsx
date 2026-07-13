import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiGet } from '../api/client';

interface MovieDetail {
    id: string;
    title: string;
    year: number;
    director: string;
    genres: {id: number; name: string}[];
    stars: {id: string; name: string}[];
    rating: number;
}

export default function SingleMovie() {
    const { id } = useParams<{ id: string }>();
    const [movie, setMovie] = useState<MovieDetail | null>(null);

    useEffect(() => {
        apiGet<MovieDetail>(`/movies/${id}`).then(setMovie);
    }, [id]);

    if (!movie) return <p>Loading...</p>;

    return (
        <div>
            <h1>{movie.title} ({movie.year})</h1>
            <p>Director: {movie.director}</p>
            <p>Rating: {movie.rating}</p>
            <p>Genres: {movie.genres.map((g) => g.name).join(", ")}</p>
            <p>
                Stars:{" "}
                {movie.stars.map((s, i) => (
                    <span key={s.id}>
                        <Link to={`/stars/${s.id}`}>{s.name}</Link>
                        {i < movie.stars.length - 1 ? ", " : ""}
                    </span>
                ))}
            </p>
            <Link to="/">Back to Movie List</Link>
        </div>
    );
}