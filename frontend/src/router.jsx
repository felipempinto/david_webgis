import { createBrowserRouter } from "react-router-dom";
import Map from "./pages/MapPage"
// import Login from "./pages/Login";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <Map />
    },
    // {
    //     path: "/login",
    //     element: <Login />
    // }
]);
