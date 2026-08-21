import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AddToCartButton from "../components/AddToCartButton";
import SearchForm from "../components/SearchForm";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import {
    ChevronLeftIcon,
    ChevronRightIcon,
    CloseIcon,
    SearchIcon,
    SortIcon,
} from "../components/ui/Icons";
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
    price: number;
}
interface MovieListResponse {
    items: MovieListItem[];
    total: number;
    page: number;
    limit: number;
}

type SortField = "title" | "year" | "rating" | "price";

const PAGE_SIZES = [10, 25, 50, 100];
const LETTERS = [
    ...Array.from({ length: 10 }, (_, i) => String(i)),
    ...Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i)),
];
const SYMBOL_KEY = "*";
const FILTER_KEYS = ["title", "year", "director", "star", "genreId", "startsWith"] as const;

export default function MovieList() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [data, setData] = useState<MovieListResponse | null>(null);
    const [genres, setGenres] = useState<Genre[]>([]);

    const page = Number(searchParams.get("page") ?? "1");
    const sortBy = searchParams.get("sortBy") ?? "rating";
    const sortDir = searchParams.get("sortDir") ?? "desc";
    const activeGenreId = searchParams.get("genreId");
    const activeLetter = searchParams.get("startsWith");
    const [browseOpen, setBrowseOpen] = useState(Boolean(activeGenreId || activeLetter));

    useEffect(() => {
        apiGet<Genre[]>("/genres").then(setGenres);
    }, []);

    useEffect(() => {
        setData(null);
        apiGet<MovieListResponse>(`/movies?${searchParams.toString()}`).then(setData);
    }, [searchParams]);

    const updateParam = (key: string, value: string) => {
        const next = new URLSearchParams(searchParams);
        next.set(key, value);
        if (key !== "page") next.set("page", "1"); // any filter/sort/page-size change resets to page 1
        setSearchParams(next);
    };

    const removeParam = (key: string) => {
        const next = new URLSearchParams(searchParams);
        next.delete(key);
        next.set("page", "1");
        setSearchParams(next);
    };

    const toggleParam = (key: string, value: string) => {
        if (searchParams.get(key) === value) removeParam(key);
        else updateParam(key, value);
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

    const toggleSort = (field: SortField) => {
        const nextDir = sortBy === field && sortDir === "asc" ? "desc" : "asc";
        const next = new URLSearchParams(searchParams);
        next.set("sortBy", field);
        next.set("sortDir", nextDir);
        next.set("page", "1");
        setSearchParams(next);
    };

    const sortableHeader = (field: SortField, label: string, numeric = false) => {
        const active = sortBy === field;
        const direction = active ? (sortDir === "asc" ? "asc" : "desc") : null;
        return (
            <th
                scope="col"
                className={numeric ? "num" : undefined}
                aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
            >
                <button
                    type="button"
                    className={numeric ? "th-sort th-sort--num" : "th-sort"}
                    onClick={() => toggleSort(field)}
                    aria-label={`Sort by ${label}, ${
                        direction === "asc" ? "currently ascending" : direction === "desc" ? "currently descending" : "not sorted"
                    }`}
                >
                    {label}
                    <SortIcon className="th-sort__icon" direction={direction} />
                </button>
            </th>
        );
    };

    const filterLabel = (key: string, value: string) => {
        if (key === "genreId") return `Genre: ${genres.find((g) => String(g.id) === value)?.name ?? value}`;
        if (key === "startsWith")
            return value === SYMBOL_KEY ? "Starts with: symbol" : `Starts with: ${value}`;
        return `${key.charAt(0).toUpperCase()}${key.slice(1)}: ${value}`;
    };

    const browseHint = [
        activeGenreId && genres.find((g) => String(g.id) === activeGenreId)?.name,
        activeLetter && (activeLetter === SYMBOL_KEY ? "Symbols" : activeLetter),
    ]
        .filter(Boolean)
        .join(" · ");

    const activeFilters = FILTER_KEYS.filter((key) => searchParams.get(key)).map((key) => ({
        key,
        value: searchParams.get(key) as string,
    }));

    const searchInitial = Object.fromEntries(
        (["title", "year", "director", "star"] as const)
            .map((key) => [key, searchParams.get(key) ?? ""])
            .filter(([, value]) => value),
    ) as Record<string, string>;

    const totalPages = data ? Math.max(1, Math.ceil(data.total / data.limit)) : 1;
    const backState = { from: `/?${searchParams.toString()}` };
    const limit = Number(searchParams.get("limit") ?? "10");

    return (
        <>
            <div className="page-head">
                <h1>Movies</h1>
                {data && (
                    <p className="page-head__meta">
                        {data.total.toLocaleString()} {data.total === 1 ? "title" : "titles"}
                    </p>
                )}
            </div>

            <div className="filters">
                <SearchForm onSearch={replaceFilters} initial={searchInitial} />

                <details
                    className="browse"
                    open={browseOpen}
                    onToggle={(e) => setBrowseOpen(e.currentTarget.open)}
                >
                    <summary className="browse__summary">
                        Browse by genre or letter
                        {browseHint && <span className="browse__hint">{browseHint}</span>}
                    </summary>

                    <div className="browse__body">
                        <div className="filters__group">
                            <h2 className="section-label" id="browse-genre">
                                Genre
                            </h2>
                            <div className="chip-row" role="group" aria-labelledby="browse-genre">
                                {genres.map((g) => (
                                    <button
                                        key={g.id}
                                        type="button"
                                        className="chip"
                                        aria-pressed={activeGenreId === String(g.id)}
                                        onClick={() => toggleParam("genreId", String(g.id))}
                                    >
                                        {g.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="filters__group">
                            <h2 className="section-label" id="browse-title">
                                Title starts with
                            </h2>
                            <div className="chip-row" role="group" aria-labelledby="browse-title">
                                {LETTERS.map((c) => (
                                    <button
                                        key={c}
                                        type="button"
                                        className="chip chip--letter"
                                        aria-pressed={activeLetter === c}
                                        aria-label={`Titles starting with ${c}`}
                                        onClick={() => toggleParam("startsWith", c)}
                                    >
                                        {c}
                                    </button>
                                ))}
                                <button
                                    type="button"
                                    className="chip"
                                    aria-pressed={activeLetter === SYMBOL_KEY}
                                    aria-label="Titles starting with a symbol"
                                    onClick={() => toggleParam("startsWith", SYMBOL_KEY)}
                                >
                                    Other
                                </button>
                            </div>
                        </div>
                    </div>
                </details>

                {activeFilters.length > 0 && (
                    <div className="active-filters">
                        <span className="active-filters__label">Active</span>
                        {activeFilters.map(({ key, value }) => (
                            <button
                                key={key}
                                type="button"
                                className="filter-pill"
                                onClick={() => removeParam(key)}
                                aria-label={`Remove filter ${filterLabel(key, value)}`}
                            >
                                {filterLabel(key, value)}
                                <CloseIcon size={12} />
                            </button>
                        ))}
                        <Button variant="ghost" size="sm" onClick={() => replaceFilters({})}>
                            Clear all
                        </Button>
                    </div>
                )}
            </div>

            {data && data.items.length === 0 ? (
                <div className="panel">
                    <EmptyState
                        icon={<SearchIcon size={32} />}
                        title="No movies match these filters"
                        body="Try removing a filter, or search for a different title, director, or star."
                        action={
                            <Button variant="secondary" onClick={() => replaceFilters({})}>
                                Clear all filters
                            </Button>
                        }
                    />
                </div>
            ) : (
                <div className="table-wrap">
                    <table className="table">
                        <caption className="visually-hidden">
                            Movies, sorted by {sortBy} {sortDir === "asc" ? "ascending" : "descending"}
                        </caption>
                        <thead>
                            <tr>
                                {sortableHeader("title", "Title")}
                                {sortableHeader("year", "Year", true)}
                                <th scope="col">
                                    <span className="th-label">Director</span>
                                </th>
                                <th scope="col">
                                    <span className="th-label">Genres</span>
                                </th>
                                <th scope="col">
                                    <span className="th-label">Stars</span>
                                </th>
                                {sortableHeader("rating", "Rating", true)}
                                {sortableHeader("price", "Price", true)}
                                <th scope="col" className="shrink">
                                    <span className="visually-hidden">Actions</span>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {!data
                                ? Array.from({ length: Math.min(limit, 10) }, (_, i) => (
                                      <tr key={`skeleton-${i}`}>
                                          {Array.from({ length: 8 }, (_, c) => (
                                              <td key={c}>
                                                  <span className="skeleton" />
                                              </td>
                                          ))}
                                      </tr>
                                  ))
                                : data.items.map((m) => (
                                      <tr key={m.id}>
                                          <td>
                                              <Link className="title-cell" to={`/movies/${m.id}`} state={backState}>
                                                  {m.title}
                                              </Link>
                                          </td>
                                          <td className="num">{m.year}</td>
                                          <td>{m.director}</td>
                                          <td>
                                              <span className="cell-links cell-links--tight">
                                                  {m.genres.map((g) => (
                                                      <button
                                                          key={g.id}
                                                          type="button"
                                                          className="tag"
                                                          onClick={() => toggleParam("genreId", String(g.id))}
                                                      >
                                                          {g.name}
                                                      </button>
                                                  ))}
                                              </span>
                                          </td>
                                          <td>
                                              <span className="cell-links cell-links--tight">
                                                  {m.stars.map((s, i) => (
                                                      <span key={s.id}>
                                                          <Link className="link-quiet" to={`/stars/${s.id}`} state={backState}>
                                                              {s.name}
                                                          </Link>
                                                          {i < m.stars.length - 1 ? "," : ""}
                                                      </span>
                                                  ))}
                                              </span>
                                          </td>
                                          <td className="num">{m.rating?.toFixed(1) ?? "—"}</td>
                                          <td className="num">${m.price.toFixed(2)}</td>
                                          <td className="shrink">
                                              <AddToCartButton movieId={m.id} />
                                          </td>
                                      </tr>
                                  ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="pagination">
                <Button
                    disabled={!data || page <= 1}
                    onClick={() => updateParam("page", String(page - 1))}
                >
                    <ChevronLeftIcon size={15} />
                    Prev
                </Button>
                <span className="pagination__status">
                    Page {page} of {totalPages}
                </span>
                <Button
                    disabled={!data || page >= totalPages}
                    onClick={() => updateParam("page", String(page + 1))}
                >
                    Next
                    <ChevronRightIcon size={15} />
                </Button>
                <label className="pagination__size">
                    Show
                    <select
                        className="input"
                        value={limit}
                        onChange={(e) => updateParam("limit", e.target.value)}
                    >
                        {PAGE_SIZES.map((n) => (
                            <option key={n} value={n}>
                                {n} per page
                            </option>
                        ))}
                    </select>
                </label>
            </div>
        </>
    );
}
