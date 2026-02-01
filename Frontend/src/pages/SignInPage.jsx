import { SignIn } from '@clerk/clerk-react';
import './AuthPage.css';

const SignInPage = () => {
    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="auth-header">
                    <img src="/logo.png" alt="AtherOps" className="auth-logo" />
                    <p className="auth-subtitle">Multi-Agent Healing System</p>
                </div>
                <SignIn
                    appearance={{
                        elements: {
                            rootBox: 'clerk-root',
                            card: 'clerk-card'
                        }
                    }}
                    routing="path"
                    path="/sign-in"
                    signUpUrl="/sign-up"
                />
            </div>
        </div>
    );
};

export default SignInPage;
