import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.jsx'

const Root = () => {
  const [publishableKey, setPublishableKey] = useState(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || null);
  const [loading, setLoading] = useState(!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);
  const [error, setError] = useState(null);

  useEffect(() => {
    // If key is already present (dev mode), don't fetch
    if (publishableKey) return;

    // Fetch config from backend for runtime injection
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        if (data.clerkPublishableKey) {
          setPublishableKey(data.clerkPublishableKey);
        } else {
          setError("No Clerk Publishable Key found in configuration.");
        }
      })
      .catch(err => {
        console.error("Failed to load config:", err);
        // Fallback to local fallback if provided or show error
        setError(`Failed to load configuration: ${err.message}`);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'white' }}>Loading Configuration...</div>;
  }

  if (error) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'red', flexDirection: 'column', gap: '1rem' }}>
      <h2>Configuration Error</h2>
      <p>{error}</p>
      <p style={{ fontSize: '0.9rem', color: '#888' }}>Make sure .env file exists and contains CLERK_PUBLISHABLE_KEY</p>
    </div>;
  }

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      afterSignOutUrl="/sign-in"
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInForceRedirectUrl="/dashboard"
      signUpForceRedirectUrl="/dashboard"
    >
      <App />
    </ClerkProvider>
  );
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Root />
    </BrowserRouter>
  </StrictMode>,
)
