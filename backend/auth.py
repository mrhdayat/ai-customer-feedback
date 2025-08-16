from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
import logging
from config import settings
from database import DatabaseService
from models import UserRole

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """Verify JWT token from Supabase"""
        try:
            token = credentials.credentials
            
            # For demo purposes, we'll implement a simple token verification
            # In production, you'd verify against Supabase JWT
            payload = jwt.decode(
                token, 
                settings.backend_secret_key, 
                algorithms=[settings.backend_algorithm]
            )
            
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_user(self, token_data: dict = Depends(verify_token)) -> dict:
        """Get current user from token"""
        user_id = token_data.get("sub")
        user_profile = await self.db_service.get_user_profile(user_id)
        
        if user_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_profile
    
    async def require_role(self, required_roles: list[UserRole]):
        """Decorator to require specific roles"""
        def role_checker(current_user: dict = Depends(self.get_current_user)):
            user_role = UserRole(current_user.get("role"))
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return role_checker
    
    async def get_optional_user(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
        """Get user if authenticated, otherwise return None (for demo access)"""
        if credentials is None:
            return None
        
        try:
            token_data = await self.verify_token(credentials)
            return await self.get_current_user(token_data)
        except HTTPException:
            return None


# Global auth service instance
auth_service = AuthService()

# Common dependencies
async def get_current_user(current_user: dict = Depends(auth_service.get_current_user)):
    return current_user

async def get_optional_user(user: Optional[dict] = Depends(auth_service.get_optional_user)):
    return user

async def require_member_or_admin(current_user: dict = Depends(auth_service.require_role([UserRole.MEMBER, UserRole.ADMIN]))):
    return current_user

async def require_admin(current_user: dict = Depends(auth_service.require_role([UserRole.ADMIN]))):
    return current_user


def create_demo_token(user_id: str, email: str, role: str) -> str:
    """Create a demo JWT token for testing"""
    from datetime import datetime, timedelta
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    
    return jwt.encode(payload, settings.backend_secret_key, algorithm=settings.backend_algorithm)
