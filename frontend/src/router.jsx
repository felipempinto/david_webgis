import { createBrowserRouter } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import MapPage from "./pages/MapPage";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import ProtectedRoute from "./pages/ProtectedRoute"

export const router = createBrowserRouter([
    {
        path: "/",
        element: <LandingPage />
    },

    {
        path: "/map",
        element: (
            <ProtectedRoute>
                <MapPage />
            </ProtectedRoute>
        )
    },

    {
        path: "/login",
        element: <LoginPage />
    },

    {
        path: "/register",
        element: <RegisterPage />
    }

]);


// import { createBrowserRouter } from "react-router-dom";
// import Map from "./pages/MapPage"
// import LoginPage from "./pages/Login";
// import RegisterPage from "./pages/Register";

// export const router = createBrowserRouter([
//     {
//         path: "/",
//         element: <Map />
//     },
//     {
//         path: "/login",
//         element: <LoginPage />
//     },
//     {
//         path: "/register",
//         element: <RegisterPage />
//     },
    
// ]);
