import { useNavigate } from "react-router-dom";
import "./LandingPage.css";

const LandingPage = () => {
    const navigate = useNavigate();
    return (
        <div className="landing-container">
            <div className="landing-card">
                <h1>Welcome</h1>
                <p>You must login to access the map</p>
                <div className="landing-buttons">
                    <button
                        onClick={() => navigate("/login")}
                    >
                        Login
                    </button>
                    <button
                        onClick={() => navigate("/register")}
                    >
                        Register
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LandingPage;