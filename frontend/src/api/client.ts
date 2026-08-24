const API_BASE = import.meta.env.VITE_API_BASE;

const REQUEST_TIMEOUT_MS = 15_000;

export class ApiError extends Error {
    readonly status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

const NETWORK_STATUS = 0;
const TIMEOUT_STATUS = -1;

function statusMessage(status: number): string {
    if (status === 404) return "We couldn't find what you were looking for.";
    if (status === 401 || status === 403) return "You don't have access to this.";
    if (status >= 500) return "The server had a problem. Please try again in a moment.";
    return `Request failed with status ${status}.`;
}

export function isAuthRedirect(error: unknown): boolean {
    return (
        error instanceof ApiError &&
        error.status === 401 &&
        window.location.pathname !== "/login"
    );
}

export function errorMessage(error: unknown): string {
    if (error instanceof ApiError) return error.message;
    return "Something went wrong. Please try again.";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE}${path}`, {
            credentials: "include",
            signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
            ...options,
            headers: { "Content-Type": "application/json", ...options.headers },
        });
    } catch (error) {
        if (error instanceof DOMException && error.name === "TimeoutError") {
            throw new ApiError(
                "The server took too long to respond. Please try again.",
                TIMEOUT_STATUS,
            );
        }
        throw new ApiError(
            "Can't reach the server. Check your connection and try again.",
            NETWORK_STATUS,
        );
    }

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = (body as { detail?: unknown } | null)?.detail;
        const message = typeof detail === "string" ? detail : statusMessage(response.status);
        if (response.status === 401 && window.location.pathname !== "/login") {
            window.location.href = "/login";
        }
        throw new ApiError(message, response.status);
    }

    if (response.status === 204) return undefined as T;
    return response.json();
}

export const apiGet = <T,>(path: string) => request<T>(path);
export const apiPost = <T,>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined });
export const apiDelete = <T,>(path: string) => request<T>(path, { method: "DELETE" });
