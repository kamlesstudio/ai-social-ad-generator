"""
Authentication Models
"""

from pydantic import BaseModel, Field
from typing import Optional

class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., description="Phone number with country code (e.g., +919876543210)")

class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., description="Phone number")
    otp: str = Field(..., description="6-digit OTP")

class UserRegisterRequest(BaseModel):
    phone: str = Field(..., description="Phone number")
    name: str = Field(..., description="User's full name")
    email: Optional[str] = Field(None, description="Email address (optional)")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class OTPResponse(BaseModel):
    status: str
    message: str
    phone: str
    expires_in: int = 300  # 5 minutes