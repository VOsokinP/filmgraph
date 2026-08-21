import { useState, type SubmitEvent } from "react";

import Button from "./ui/Button";
import Field from "./ui/Field";
import { SearchIcon } from "./ui/Icons";

interface Props {
    onSearch: (params: Record<string, string>) => void;
    initial?: Record<string, string>;
}

export default function SearchForm({ onSearch, initial }: Props) {
    const [title, setTitle] = useState(initial?.title ?? "");
    const [year, setYear] = useState(initial?.year ?? "");
    const [director, setDirector] = useState(initial?.director ?? "");
    const [star, setStar] = useState(initial?.star ?? "");

    const submit = (event: SubmitEvent) => {
        event.preventDefault();
        const params: Record<string, string> = {};
        if (title) params.title = title;
        if (year) params.year = year;
        if (director) params.director = director;
        if (star) params.star = star;
        onSearch(params);
    };

    const clear = () => {
        setTitle("");
        setYear("");
        setDirector("");
        setStar("");
        onSearch({});
    };

    const hasInput = Boolean(title || year || director || star);

    return (
        <form className="search-grid" onSubmit={submit}>
            <Field
                label="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Any part of the title"
                autoComplete="off"
            />
            <Field
                label="Year"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                placeholder="e.g. 1982"
                inputMode="numeric"
                pattern="[0-9]*"
                autoComplete="off"
            />
            <Field
                label="Director"
                value={director}
                onChange={(e) => setDirector(e.target.value)}
                placeholder="Any part of the name"
                autoComplete="off"
            />
            <Field
                label="Star"
                value={star}
                onChange={(e) => setStar(e.target.value)}
                placeholder="Any part of the name"
                autoComplete="off"
            />
            <div className="search-grid__actions">
                <Button type="submit" variant="primary">
                    <SearchIcon size={15} />
                    Search
                </Button>
                <Button variant="ghost" onClick={clear} disabled={!hasInput}>
                    Clear
                </Button>
            </div>
        </form>
    );
}
