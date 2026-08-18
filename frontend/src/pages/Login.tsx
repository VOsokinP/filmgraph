import { useState, type SubmitEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { apiPost } from '../api/client';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const { refresh } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (event: SubmitEvent) => {
        event.preventDefault();
        setError(null);
        try {
            await apiPost('/auth/login', { email, password });
            await refresh();
            navigate('/');
        } catch {
            setError('Invalid email or password');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h1>Log In</h1>
            <label>
                Email
                <input type="email" value = {email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
                Password
                <input type="password" value = {password} onChange={(e) => setPassword(e.target.value)} required />
            </label>
            {error && <p role = "alert">{error}</p>}
            <button type="submit">Log In</button>
        </form>
    );
}