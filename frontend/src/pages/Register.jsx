import { useState } from "react";
import { register } from "../api/auth";
import "./auth.css";

const RegisterPage = () => {
    const [email,setEmail] = useState("");
    const [password,setPassword] = useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await register(email,password);
            alert("Account created");
            window.location.href="/login";
        } catch(err){
            alert(err.message);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Create Account</h2>
                <form onSubmit={handleSubmit}>
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e)=>setEmail(e.target.value)}
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e)=>setPassword(e.target.value)}
                    />
                    <button type="submit">
                        Register
                    </button>
                </form>
            </div>
        </div>
    );
};

export default RegisterPage;