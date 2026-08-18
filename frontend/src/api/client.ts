const API_BASE = import.meta.env.VITE_API_BASE;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
        credentials: "include",
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (response.status === 401) {
        if (window.location.pathname !== "/login") {
        window.location.href = "/login";
    }
    throw new Error("Not authenticated");
    }
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `API request failed with status ${response.status}`);
    }
    if (response.status === 204) return undefined as T;
    return response.json();
}

export const apiGet = <T,>(path: string) => request<T>(path);
export const apiPost = <T,>(path: string, data?: unknown) => 
    request<T>(path, { method: "POST", body: data ? JSON.stringify(data) : undefined });
export const apiDelete = <T,>(path: string) => request<T>(path, { method: "DELETE" });