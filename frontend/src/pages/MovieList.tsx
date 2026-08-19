import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AddToCartButton from "../components/AddToCartButton";
import SearchForm from "../components/SearchForm";
import { apiGet } from "../api/client";


interface Genre { id: number; name: string }
interface Star { id: string; name: string }
interface MovieListItem {
    id: string;
    title: string;
    year: number;
    director: string;
    genres: Genre[];
    stars: Star[];
    rating: number | null;
}
interface MovieListResponse {
    items: MovieListItem[];
    total: number;
    page: number;
    limit: number;
}

const PAGE_SIZES = [10, 25, 50, 100];
const ALPHABET = [
    "*",
    ...Array.from({ length: 10 }, (_, i) => String(i)),
    ...Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i)),
];

export default function MovieList() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [data, setData] = useState<MovieListResponse | null>(null);
    const [genres, setGenres] = useState<Genre[]>([]);

    const page = Number(searchParams.get("page") ?? "1");
    const sortBy = searchParams.get("sortBy") ?? "rating";
    const sortDir = searchParams.get("sortDir") ?? "desc";

    useEffect(() => {
        apiGet<Genre[]>("/genres").then(setGenres);
    }, []);
    
    useEffect(() => {
        apiGet<MovieListResponse>(`/movies?${searchParams.toString()}`).then(setData);
    }, [searchParams]);

    const updateParam = (key: string, value: string) => {
        const next = new URLSearchParams(searchParams);
        next.set(key, value);
        if (key !== "page") next.set("page", "1"); // any filter/sort/page-size change resets to page 1
        setSearchParams(next);
    };

    const replaceFilters = (params: Record<string, string>) => {
        const next = new URLSearchParams();
        next.set("sortBy", sortBy);
        next.set("sortDir", sortDir);
        next.set("limit", searchParams.get("limit") ?? "10");
        next.set("page", "1");
        Object.entries(params).forEach(([key, value]) => next.set(key, value));
        setSearchParams(next);
    };

    const toggleSort = (field: "title" | "rating") => {
        const nextDir = sortBy === field && sortDir === "asc" ? "desc" : "asc";
        const next = new URLSearchParams(searchParams);
        next.set("sortBy", field);
        next.set("sortDir", nextDir);
        next.set("page", "1");
        setSearchParams(next);
    };

    if (!data) return <p>Loading…</p>;

    const totalPages = Math.max(1, Math.ceil(data.total / data.limit));
    const backState = { from: `/?${searchParams.toString()}` };

    return (
        <div>
            <SearchForm onSearch={replaceFilters} />
            <section> 
                <h2>Browse by genre</h2>
                {genres.map((g) => (
                    <button key = {g.id} onClick = {() => updateParam("genreId", String(g.id))}>
                        {g.name}
                    </button>
                ))}
            </section>

            <section>
                <h2>Browse by title</h2>
                {ALPHABET.map((c) => (
                    <button key = {c} onClick = {() => updateParam("startsWith", c)}>
                        {c}
                    </button>
                ))}
            </section>

            <table>
                <thead>
                    <tr>
                        <th onClick = {() => toggleSort("title")}>Title</th>
                        <th>Year</th>
                        <th>Director</th>
                        <th>Genres</th>
                        <th>Stars</th>
                        <th onClick = {() => toggleSort("rating")}>Rating</th>
                        <th />
                    </tr>
                </thead>
                <tbody>
                    {data.items.map((m) => (
                        <tr key = {m.id}>
                            <td>
                                <Link to = {`/movies/${m.id}`} state = {backState}>{m.title}</Link>
                            </td>
                            <td>{m.year}</td>
                            <td>{m.director}</td>
                            <td>
                                {m.genres.map((g, i) => (
                                    <span key = {g.id}>
                                        <button onClick = {() => updateParam("genreId", String(g.id))}>{g.name}</button>
                                        {i < m.genres.length - 1 ? ", " : ""}
                                    </span>
                                ))}
                            </td>
                            <td>
                                {m.stars.map((s, i) => (
                                    <span key = {s.id}>
                                        <Link to = {`/stars/${s.id}`} state = {backState}>{s.name}</Link>
                                        {i < m.stars.length - 1 ? ", " : ""}
                                    </span>
                                ))}
                            </td>
                            <td>{m.rating ?? "N/A"}</td>
                            <td>
                                <AddToCartButton movieId = {m.id} />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <div>
                <button disabled = {page <= 1} onClick = {() => updateParam("page", String(page - 1))}>
                    Prev
                </button>
                <span>
                    Page {page} of {totalPages}
                </span>
                <button disabled = {page >= totalPages} onClick = {() => updateParam("page", String(page + 1))}>
                    Next
                </button>
                <select value = {data.limit} onChange = {(e) => updateParam("limit", e.target.value)}>
                    {PAGE_SIZES.map((n) => (
                        <option key = {n} value = {n}>
                            {n} per page
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
}