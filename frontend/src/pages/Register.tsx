import { useState, type SubmitEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { apiPost, errorMessage } from '../api/client';
import Button from '../components/ui/Button';
import Field from '../components/ui/Field';
import { AlertIcon, ChevronLeftIcon, FilmIcon } from '../components/ui/Icons';

const MIN_PASSWORD_LENGTH = 8;

export default function Register() {
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
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
            await apiPost('/auth/register', { firstName, lastName, email, password });
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
                <h1 className="auth__title">Create an account</h1>

                <form className="form" onSubmit={handleSubmit}>
                    <div className="form__row">
                        <Field
                            label="First name"
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            autoComplete="given-name"
                            required
                        />
                        <Field
                            label="Last name"
                            value={lastName}
                            onChange={(e) => setLastName(e.target.value)}
                            autoComplete="family-name"
                            required
                        />
                    </div>
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
                        autoComplete="new-password"
                        minLength={MIN_PASSWORD_LENGTH}
                        required
                    />
                    {error && (
                        <p className="alert alert--error" role="alert">
                            <AlertIcon size={16} className="alert__icon" />
                            {error}
                        </p>
                    )}
                    <Button type="submit" variant="primary" block pending={pending}>
                        Create account
                    </Button>
                </form>

                <p className="auth__alt">
                    Already have an account?{' '}
                    <Link to="/login" state={{ from }} className="link-quiet">
                        Log in
                    </Link>
                </p>

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
