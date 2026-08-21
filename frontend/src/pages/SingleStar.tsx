import { useEffect, useState } from 'react';
import { Link, useParams, useLocation } from 'react-router-dom';

import EmptyState from '../components/ui/EmptyState';
import { ChevronLeftIcon, FilmIcon } from '../components/ui/Icons';
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
    const backTo = (location.state as { from?: string } | null)?.from ?? "/";
    const [star, setStar] = useState<StarDetail | null>(null);

    useEffect(() => {
        apiGet<StarDetail>(`/stars/${id}`).then(setStar);
    }, [id]);

    if (!star) {
        return (
            <div className="stack-sm" aria-busy="true">
                <span className="skeleton" style={{ width: '12ch' }} />
                <span className="skeleton" style={{ width: '30%', height: '2em' }} />
                <span className="skeleton" style={{ width: '50%' }} />
            </div>
        );
    }

    return (
        <>
            <Link to={backTo} className="back-link">
                <ChevronLeftIcon size={15} />
                Back to movie list
            </Link>

            <div className="page-head">
                <div>
                    <h1>{star.name}</h1>
                    <p className="detail__subtitle" style={{ marginBottom: 0 }}>
                        Born {star.birth_year ?? 'unknown'}
                    </p>
                </div>
                <p className="page-head__meta">
                    {star.movies.length} {star.movies.length === 1 ? 'credit' : 'credits'}
                </p>
            </div>

            {star.movies.length === 0 ? (
                <div className="panel">
                    <EmptyState
                        icon={<FilmIcon size={32} />}
                        title="No movie credits on record"
                        body="This star has no linked titles in the catalog yet."
                    />
                </div>
            ) : (
                <div className="table-wrap">
                    <table className="table">
                        <caption className="visually-hidden">Filmography for {star.name}</caption>
                        <thead>
                            <tr>
                                <th scope="col">
                                    <span className="th-label">Title</span>
                                </th>
                                <th scope="col" className="num">
                                    <span className="th-label">Year</span>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {star.movies.map((m) => (
                                <tr key={m.id}>
                                    <td>
                                        <Link className="title-cell" to={`/movies/${m.id}`} state={{ from: backTo }}>
                                            {m.title}
                                        </Link>
                                    </td>
                                    <td className="num">{m.year}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
