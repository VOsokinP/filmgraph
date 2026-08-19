import { useState, type SubmitEvent } from "react";

interface Props {
    onSearch: (params: Record<string, string>) => void;
}

export default function SearchForm({ onSearch }: Props) {
    const [title, setTitle] = useState("");
    const [year, setYear] = useState("");
    const [director, setDirector] = useState("");
    const [star, setStar] = useState("");

    const submit = (event: SubmitEvent) => {
        event.preventDefault();
        const params: Record<string, string> = {};
        if (title) params.title = title;
        if (year) params.year = year;
        if (director) params.director = director;
        if (star) params.star = star;
        onSearch(params);
    };

    return (
        <form onSubmit={submit}>
            <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <input placeholder="Year" value={year} onChange={(e) => setYear(e.target.value)} />
            <input placeholder="Director" value={director} onChange={(e) => setDirector(e.target.value)} />
            <input placeholder="Star" value={star} onChange={(e) => setStar(e.target.value)} />
            <button type="submit">Search</button>
        </form>
    );
}