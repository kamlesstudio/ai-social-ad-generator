"""
Authentication Routes - Fixed to use Database
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()

# Import from services
from app.services.auth_service import auth_service, otp_storage
from app.models.database import db_service  # ✅ Add database service

# Models
from pydantic import BaseModel
from typing import Optional

class PhoneLoginRequest(BaseModel):
    phone: str

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str

class UserRegisterRequest(BaseModel):
    phone: str
    name: str
    email: Optional[str] = None

class OTPResponse(BaseModel):
    status: str
    message: str
    phone: str
    expires_in: int = 300

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(request: PhoneLoginRequest):
    """Send OTP to the provided phone number"""
    if not request.phone or len(request.phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )
    
    otp = auth_service.generate_otp()
    success = auth_service.send_otp_via_fast2sms(request.phone, otp)
    
    if not success:
        logger.info(f"📱 OTP for {request.phone}: {otp}")
    
    auth_service.store_otp(request.phone, otp)
    
    return OTPResponse(
        status="success",
        message="OTP sent successfully" if success else "OTP sent (development mode)",
        phone=request.phone,
        expires_in=300
    )

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP and return JWT token"""
    if not auth_service.verify_otp(request.phone, request.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    # ✅ Use DATABASE instead of in-memory storage
    user_data = db_service.get_user(request.phone)
    
    if not user_data:
        # Create user in database with 0 credits
        user_data = db_service.create_user(request.phone, {
            "name": request.phone,
            "credits": 0  # Start with 0 credits
        })

        credits = db_service.check_and_give_welcome_credits(request.phone)
        user_data["credits"] = credits
        logger.info(f"📝 New user created: {request.phone} with 0 credits")
    
    token_data = {
        "sub": request.phone,
        "phone": request.phone,
        "name": user_data.get("name", request.phone)
    }
    access_token = auth_service.create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data
    )

@router.get("/test-otp/{phone}")
async def test_get_otp(phone: str):
    """Test endpoint to get OTP (development only)"""
    if phone in otp_storage:
        return {
            "phone": phone,
            "otp": otp_storage[phone]["otp"],
            "expiry": otp_storage[phone]["expiry"]
        }
    return {"message": "No OTP found for this phone"}