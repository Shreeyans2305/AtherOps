"""
Authentication middleware for Clerk JWT verification.
"""
import os
import jwt
import requests
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

security = HTTPBearer()

# Clerk configuration
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")

# Extract domain from publishable key
# Format: pk_test_<base64>
if CLERK_PUBLISHABLE_KEY:
    # Clerk JWKS URL
    CLERK_JWKS_URL = f"https://api.clerk.com/v1/jwks"
else:
    CLERK_JWKS_URL = None


@lru_cache(maxsize=1)
def get_jwks() -> Dict:
    """
    Fetch and cache Clerk's JWKS (JSON Web Key Set).
    """
    if not CLERK_JWKS_URL:
        raise ValueError("Clerk JWKS URL not configured")
    
    response = requests.get(CLERK_JWKS_URL)
    response.raise_for_status()
    return response.json()


def verify_clerk_token(token: str) -> Dict:
    """
    Verify a Clerk JWT token and extract user information.
    
    Args:
        token: JWT token from Clerk
        
    Returns:
        Dict containing user_id, org_id, email, etc.
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode without verification first to get the header
        unverified_header = jwt.get_unverified_header(token)
        
        # Get JWKS
        jwks = get_jwks()
        
        # Find the key that matches the token's kid
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
        
        # Verify and decode the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Clerk doesn't use standard aud claim
        )
        
        # Extract user information
        user_info = {
            "user_id": payload.get("sub"),
            "org_id": payload.get("org_id"),
            "email": payload.get("email"),
            "session_id": payload.get("sid"),
            "azp": payload.get("azp"),  # Authorized party
        }
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTClaimsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    FastAPI dependency to get the current authenticated user.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    token = credentials.credentials
    return verify_clerk_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict]:
    """
    FastAPI dependency to get the current user if authenticated, None otherwise.
    Useful for routes that work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        return verify_clerk_token(credentials.credentials)
    except HTTPException:
        return None


def require_organization(user: Dict = Depends(get_current_user)) -> Dict:
    """
    Require that the user belongs to an organization.
    
    Usage:
        @app.get("/org-only")
        async def org_route(user = Depends(require_organization)):
            org_id = user["org_id"]
    """
    if not user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership required"
        )
    return user
