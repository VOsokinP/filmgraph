import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";

interface MovieListItem {
    id: string;
    title: string;
    year: number;
    director: string;
    genres: {id: number; name: string}[];
    stars: {id: string; name: string}[];
    rating: number;
}

export default function MovieList() {
    const [movies, setMovies] = useState<MovieListItem[]>([]);

    useEffect(() => {
        apiGet<MovieListItem[]>("/movies").then(setMovies);
    }, []);

    return (
        <table>
            <tbody>
                {movies.map((m) => (
                    <tr key={m.id}>
                        <td><Link to={`/movies/${m.id}`}>{m.title}</Link></td>
                        <td>{m.year}</td>
                        <td>{m.director}</td>
                        <td>{m.genres.map((g) => g.name).join(", ")}</td>
                        <td>
                            {m.stars.map((s, i) => (
                                <span key={s.id}>
                                    <Link to={`/stars/${s.id}`}>{s.name}</Link>
                                    {i < m.stars.length - 1 ? ", " : ""}
                                </span>
                            ))}
                        </td>
                        <td>{m.rating}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}