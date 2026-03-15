import { createContext, useContext, useEffect, useState } from "react";
import { getMe, login as apiLogin, logout as apiLogout } from "../api/auth";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {

        const init = async () => {
            try {
                const me = await getMe();
                setUser(me);
            } catch {
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        init();

    }, []);

    const login = async (email, password) => {

        await apiLogin(email, password);

        const me = await getMe();

        setUser(me);
    };

    const logout = () => {
        apiLogout();
        setUser(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                login,
                logout,
                loading
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);