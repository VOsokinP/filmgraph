import { useEffect, useState, type SubmitEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { SearchIcon } from './ui/Icons';

const CARRIED_OVER = ['sortBy', 'sortDir', 'limit'] as const;

export default function HeaderSearch() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const activeTitle = searchParams.get('title') ?? '';
    const [term, setTerm] = useState(activeTitle);

    useEffect(() => {
        setTerm(activeTitle);
    }, [activeTitle]);

    const submit = (event: SubmitEvent) => {
        event.preventDefault();

        const next = new URLSearchParams();
        for (const key of CARRIED_OVER) {
            const value = searchParams.get(key);
            if (value) next.set(key, value);
        }

        const trimmed = term.trim();
        if (trimmed) next.set('title', trimmed);
        next.set('page', '1');

        navigate({ pathname: '/', search: next.toString() });
    };

    return (
        <form className="header-search" role="search" onSubmit={submit}>
            <SearchIcon size={15} className="header-search__icon" />
            <input
                type="search"
                className="header-search__input"
                value={term}
                onChange={(event) => setTerm(event.target.value)}
                placeholder="Search titles"
                aria-label="Search movie titles"
                autoComplete="off"
            />
        </form>
    );
}
