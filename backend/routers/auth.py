from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import logging
from models import APIResponse, UserProfile
from auth import create_demo_token
from database import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


@router.post("/login", response_model=APIResponse)
async def login(login_request: LoginRequest):
    """Login with email and password (demo implementation)"""
    try:
        db_service = DatabaseService()
        
        # Demo authentication - in production, use Supabase auth
        demo_users = {
            "demo@cfd.app": {
                "id": "00000000-0000-0000-0000-000000000001",
                "email": "demo@cfd.app",
                "password": "demo12345",
                "full_name": "Demo User",
                "role": "demo_viewer"
            },
            "member@cfd.app": {
                "id": "00000000-0000-0000-0000-000000000002",
                "email": "member@cfd.app",
                "password": "member12345",
                "full_name": "Member User",
                "role": "member"
            },
            "admin@cfd.app": {
                "id": "00000000-0000-0000-0000-000000000003",
                "email": "admin@cfd.app",
                "password": "admin12345",
                "full_name": "Admin User",
                "role": "admin"
            }
        }
        
        user_data = demo_users.get(login_request.email)
        if not user_data or user_data["password"] != login_request.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        access_token = create_demo_token(
            user_id=user_data["id"],
            email=user_data["email"],
            role=user_data["role"]
        )
        
        # Get user profile from database
        user_profile = await db_service.get_user_profile(user_data["id"])
        if not user_profile:
            # Create profile if it doesn't exist
            profile_data = {
                "id": user_data["id"],
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "role": user_data["role"]
            }
            await db_service.client.table("profiles").upsert(profile_data).execute()
            user_profile = profile_data
        
        return APIResponse(
            success=True,
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_profile
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout", response_model=APIResponse)
async def logout():
    """Logout (client-side token removal)"""
    return APIResponse(
        success=True,
        message="Logout successful"
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user_profile(current_user: dict = Depends(lambda: None)):
    """Get current user profile"""
    # This would normally use the auth dependency, but for demo we'll handle it differently
    return APIResponse(
        success=True,
        message="User profile retrieved",
        data=current_user
    )


@router.get("/demo-tokens", response_model=APIResponse)
async def get_demo_tokens():
    """Get demo tokens for testing (development only)"""
    try:
        demo_tokens = {
            "demo": create_demo_token(
                user_id="00000000-0000-0000-0000-000000000001",
                email="demo@cfd.app",
                role="demo_viewer"
            ),
            "member": create_demo_token(
                user_id="00000000-0000-0000-0000-000000000002",
                email="member@cfd.app",
                role="member"
            ),
            "admin": create_demo_token(
                user_id="00000000-0000-0000-0000-000000000003",
                email="admin@cfd.app",
                role="admin"
            )
        }
        
        return APIResponse(
            success=True,
            message="Demo tokens generated",
            data=demo_tokens
        )
        
    except Exception as e:
        logger.error(f"Error generating demo tokens: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
