import { SignUp } from '@clerk/clerk-react';
import './AuthPage.css';

const SignUpPage = () => {
    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="auth-header">
                    <img src="/logo.png" alt="AtherOps" className="auth-logo" />
                    <p className="auth-subtitle">Multi-Agent Healing System</p>
                </div>
                <SignUp
                    appearance={{
                        elements: {
                            rootBox: 'clerk-root',
                            card: 'clerk-card'
                        }
                    }}
                    routing="path"
                    path="/sign-up"
                    signInUrl="/sign-in"
                />
            </div>
        </div>
    );
};

export default SignUpPage;
