/**
 * Every test here maps to a defect that actually shipped. The point is not coverage, it is that
 * this layer has produced five bugs that lint, a green build and 116 backend tests all missed.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import Layout from '../Layout';
import { AuthProvider } from '../auth/AuthProvider';
import ProtectedRoute from '../auth/ProtectedRoute';
import Login from '../pages/Login';
import { API, filledCart, server, signedIn } from './server';

function renderApp(initialPath: string) {
    return render(
        <MemoryRouter initialEntries={[initialPath]}>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route element={<Layout />}>
                        <Route path="/" element={<p>catalogue</p>} />
                        <Route element={<ProtectedRoute />}>
                            <Route path="/payment" element={<p>payment page</p>} />
                        </Route>
                    </Route>
                </Routes>
            </AuthProvider>
        </MemoryRouter>,
    );
}

describe('login reports the real failure', () => {
    it('says the server is unreachable, not that the password was wrong', async () => {
        server.use(http.post(`${API}/auth/login`, () => HttpResponse.error()));
        renderApp('/login');

        await userEvent.type(screen.getByLabelText(/email/i), 'ada@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'correct-horse');
        await userEvent.click(screen.getByRole('button', { name: /log in/i }));

        const alert = await screen.findByRole('alert');
        expect(alert).toHaveTextContent(/can't reach the server/i);
        expect(alert).not.toHaveTextContent(/invalid email or password/i);
    });

    it('still says invalid credentials when the server actually rejects them', async () => {
        server.use(
            http.post(`${API}/auth/login`, () =>
                HttpResponse.json({ detail: 'Invalid email or password' }, { status: 401 }),
            ),
        );
        renderApp('/login');

        await userEvent.type(screen.getByLabelText(/email/i), 'ada@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'wrong');
        await userEvent.click(screen.getByRole('button', { name: /log in/i }));

        expect(await screen.findByRole('alert')).toHaveTextContent(/invalid email or password/i);
    });

    it('explains a rate limit instead of showing a bare status code', async () => {
        server.use(
            http.post(`${API}/auth/login`, () => new HttpResponse('<html>429</html>', { status: 429 })),
        );
        renderApp('/login');

        await userEvent.type(screen.getByLabelText(/email/i), 'ada@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'whatever');
        await userEvent.click(screen.getByRole('button', { name: /log in/i }));

        const alert = await screen.findByRole('alert');
        expect(alert).toHaveTextContent(/too many attempts/i);
        expect(alert).not.toHaveTextContent(/status 429/i);
    });
});

describe('an unreachable server is not the same as being logged out', () => {
    it('shows a retryable error on a gated route rather than redirecting to login', async () => {
        server.use(http.get(`${API}/auth/me`, () => HttpResponse.error()));
        renderApp('/payment');

        expect(await screen.findByRole('button', { name: /try again/i })).toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: /log in/i })).not.toBeInTheDocument();
    });

    it('does redirect to login when the server says 401', async () => {
        renderApp('/payment');

        expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
    });

    it('retry refetches, so recovering does not need a page reload', async () => {
        let reachable = false;
        server.use(
            http.get(`${API}/auth/me`, () =>
                reachable
                    ? HttpResponse.json({
                          id: 1,
                          firstName: 'Ada',
                          lastName: 'Lovelace',
                          email: 'ada@example.com',
                      })
                    : HttpResponse.error(),
            ),
        );
        renderApp('/payment');

        const retry = await screen.findByRole('button', { name: /try again/i });
        reachable = true;
        await userEvent.click(retry);

        expect(await screen.findByText(/payment page/i)).toBeInTheDocument();
    });
});

describe('the cart badge follows the session', () => {
    it('clears on logout without needing a page reload', async () => {
        server.use(signedIn, filledCart);
        renderApp('/');

        expect(await screen.findByText('3')).toBeInTheDocument();

        server.use(
            http.post(`${API}/auth/logout`, () => HttpResponse.json({ status: 'ok' })),
            http.get(`${API}/auth/me`, () => HttpResponse.json({ detail: 'no' }, { status: 401 })),
            http.get(`${API}/cart`, () => HttpResponse.json({ items: [], total: 0 })),
        );

        await userEvent.click(screen.getByRole('button', { name: /log out/i }));

        await waitFor(() => expect(screen.queryByText('3')).not.toBeInTheDocument());
    });
});
