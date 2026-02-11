const API_URL = import.meta.env.VITE_API_URL;

export const login = async ({ username, password }) => {
    const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
        throw new Error("Invalid credentials");
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);

    return data;
};


export const checkAuth = async () => {
    const token = localStorage.getItem("token");

    if (!token) return false;

    const res = await fetch(`${API_URL}/protected`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    return res.ok;
};
