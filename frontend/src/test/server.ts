import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const API = 'http://localhost:8000/api';

export const anonymous = http.get(`${API}/auth/me`, () =>
    HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 }),
);

export const signedIn = http.get(`${API}/auth/me`, () =>
    HttpResponse.json({ id: 1, firstName: 'Ada', lastName: 'Lovelace', email: 'ada@example.com' }),
);

export const emptyCart = http.get(`${API}/cart`, () =>
    HttpResponse.json({ items: [], total: 0 }),
);

export const filledCart = http.get(`${API}/cart`, () =>
    HttpResponse.json({
        items: [{ movie_id: 'tt1', title: 'A Film', price: 9.99, quantity: 3, subtotal: 29.97 }],
        total: 29.97,
    }),
);

export const server = setupServer(anonymous, emptyCart);
