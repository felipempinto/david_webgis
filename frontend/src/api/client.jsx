const API_URL = import.meta.env.VITE_API_URL;

export const apiFetch = async (path, options = {}) => {

    const token = localStorage.getItem("token");

    const res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            ...(options.headers || {})
        }
    });

    if (!res.ok) {
        throw new Error("API request failed");
    }

    return res.json();
};