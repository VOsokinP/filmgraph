import { Link } from 'react-router-dom';

import EmptyState from '../components/ui/EmptyState';
import { AlertIcon, FilmIcon } from '../components/ui/Icons';

export default function NotFound() {
    return (
        <div className="auth">
            <div className="auth__card card">
                <p className="auth__brand">
                    <FilmIcon size={22} className="brand__mark" />
                    FilmGraph
                </p>
                <EmptyState
                    icon={<AlertIcon size={32} />}
                    title="Page not found"
                    body="That address doesn't match anything in FilmGraph."
                    action={
                        <Link to="/" className="btn btn--primary">
                            Back to movie list
                        </Link>
                    }
                />
            </div>
        </div>
    );
}
