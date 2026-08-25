import { useState, type SubmitEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { apiPost, errorMessage } from '../api/client';
import Button from '../components/ui/Button';
import Field from '../components/ui/Field';
import { AlertIcon, ChevronLeftIcon, FilmIcon } from '../components/ui/Icons';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState(false);
    const { refresh } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const from = (location.state as { from?: string } | null)?.from ?? '/';

    const handleSubmit = async (event: SubmitEvent) => {
        event.preventDefault();
        setError(null);
        setPending(true);
        try {
            await apiPost('/auth/login', { email, password });
            await refresh();
            navigate(from, { replace: true });
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setPending(false);
        }
    };

    return (
        <div className="auth">
            <div className="auth__card card">
                <Link to="/" className="auth__brand">
                    <FilmIcon size={22} className="brand__mark" />
                    FilmGraph
                </Link>
                <h1 className="auth__title">Log in</h1>

                <form className="form" onSubmit={handleSubmit}>
                    <Field
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="username"
                        placeholder="you@example.com"
                        required
                    />
                    <Field
                        label="Password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                        required
                    />
                    {error && (
                        <p className="alert alert--error" role="alert">
                            <AlertIcon size={16} className="alert__icon" />
                            {error}
                        </p>
                    )}
                    <Button type="submit" variant="primary" block pending={pending}>
                        Log in
                    </Button>
                </form>

                <p className="auth__foot">
                    <Link to="/" className="back-link">
                        <ChevronLeftIcon size={15} />
                        Back to movie list
                    </Link>
                </p>
            </div>
        </div>
    );
}
