const API_URL = import.meta.env.VITE_API_URL;

export async function login(email, password) {

    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email,
            password
        })
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.detail || "Login failed");
    }

    localStorage.setItem("token", data.access_token);

    return data;
}


export async function register(email, password) {

    const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email,
            password
        })
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.detail || "Register failed");
    }

    return data;
}


export async function getMe() {

    const token = localStorage.getItem("token");

    const res = await fetch(`${API_URL}/auth/me`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    if (!res.ok) {
        throw new Error("Not authenticated");
    }

    return res.json();
}


export function logout() {
    localStorage.removeItem("token");
}
// const API_URL = import.meta.env.VITE_API_URL;

// export const login = async ({ username, password }) => {
//     const res = await fetch(`${API_URL}/login`, {
//         method: "POST",
//         headers: {
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify({ username, password })
//     });

//     if (!res.ok) {
//         throw new Error("Invalid credentials");
//     }

//     const data = await res.json();
//     localStorage.setItem("token", data.access_token);

//     return data;
// };


// export const checkAuth = async () => {
//     const token = localStorage.getItem("token");

//     if (!token) return false;

//     const res = await fetch(`${API_URL}/protected`, {
//         headers: {
//             Authorization: `Bearer ${token}`
//         }
//     });

//     return res.ok;
// };
