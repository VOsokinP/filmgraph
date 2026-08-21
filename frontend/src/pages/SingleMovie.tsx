import { useEffect, useState } from 'react';
import { Link, useParams, useLocation } from 'react-router-dom';
import AddToCartButton from '../components/AddToCartButton';
import { ChevronLeftIcon } from '../components/ui/Icons';
import { apiGet } from '../api/client';

interface MovieDetail {
    id: string;
    title: string;
    year: number;
    director: string;
    genres: {id: number; name: string}[];
    stars: {id: string; name: string}[];
    rating: number | null;
    price: number;
}

export default function SingleMovie() {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const backTo = (location.state as { from?: string } | null)?.from ?? "/";
    const [movie, setMovie] = useState<MovieDetail | null>(null);

    useEffect(() => {
        apiGet<MovieDetail>(`/movies/${id}`).then(setMovie);
    }, [id]);

    if (!movie) {
        return (
            <div className="stack-sm" aria-busy="true">
                <span className="skeleton" style={{ width: '12ch' }} />
                <span className="skeleton" style={{ width: '40%', height: '2em' }} />
                <span className="skeleton" style={{ width: '65%' }} />
                <span className="skeleton" style={{ width: '55%' }} />
            </div>
        );
    }

    return (
        <>
            <Link to={backTo} className="back-link">
                <ChevronLeftIcon size={15} />
                Back to movie list
            </Link>

            <div className="detail">
                <div>
                    <h1 className="detail__title">
                        {movie.title} <span className="detail__year">({movie.year})</span>
                    </h1>
                    <p className="detail__subtitle">Directed by {movie.director}</p>

                    <dl className="facts">
                        <dt>Rating</dt>
                        <dd className="num">{movie.rating?.toFixed(1) ?? 'Not rated'}</dd>

                        <dt>Genres</dt>
                        <dd>
                            <span className="cell-links">
                                {movie.genres.length === 0 ? (
                                    <span className="muted">None listed</span>
                                ) : (
                                    movie.genres.map((g) => (
                                        <Link key={g.id} className="tag" to={`/?genreId=${g.id}`}>
                                            {g.name}
                                        </Link>
                                    ))
                                )}
                            </span>
                        </dd>

                        <dt>Stars</dt>
                        <dd>
                            <span className="cell-links">
                                {movie.stars.length === 0 ? (
                                    <span className="muted">None listed</span>
                                ) : (
                                    movie.stars.map((s, i) => (
                                        <span key={s.id}>
                                            <Link className="link-quiet" to={`/stars/${s.id}`} state={{ from: backTo }}>
                                                {s.name}
                                            </Link>
                                            {i < movie.stars.length - 1 ? ',' : ''}
                                        </span>
                                    ))
                                )}
                            </span>
                        </dd>
                    </dl>
                </div>

                <aside className="panel buybox">
                    <div>
                        <span className="buybox__price">${movie.price.toFixed(2)}</span>
                    </div>
                    <AddToCartButton movieId={movie.id} variant="primary" size="md" />
                    <p className="buybox__note">Mock checkout — no real payment is processed.</p>
                </aside>
            </div>
        </>
    );
}
