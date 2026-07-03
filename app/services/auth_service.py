"""
Authentication Service with Fast2SMS OTP
"""

import os
import random
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# OTP storage
otp_storage: Dict[str, dict] = {}
user_storage: Dict[str, dict] = {}
from dotenv import load_dotenv
load_dotenv()


class AuthService:
    def __init__(self):
        self.secret_key = "your-super-secret-jwt-key-change-this-in-production"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24 * 7
        
        self.fast2sms_api_key = os.getenv("FAST2SMS_API_KEY")
        self.fast2sms_template_id = os.getenv("FAST2SMS_TEMPLATE_ID")
        self.fast2sms_sender_id = os.getenv("FAST2SMS_SENDER_ID", "ADGEN")
        self.fast2sms_route = os.getenv("FAST2SMS_ROUTE", "dlt")
        
        if not self.fast2sms_api_key:
            logger.warning("⚠️ FAST2SMS_API_KEY not set")
    
    def generate_otp(self) -> str:
        return str(random.randint(100000, 999999))
    
    def send_otp_via_fast2sms(self, phone: str, otp: str) -> bool:
        try:
            import requests
            if phone.startswith("+"):
                phone = phone[1:]
            
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": self.fast2sms_route,
                "sender_id": self.fast2sms_sender_id,
                "message": f"Your OTP for AI Ad Generator is {otp}. Valid for 5 minutes.",
                "language": "english",
                "numbers": phone,
            }
            if self.fast2sms_template_id:
                payload["template_id"] = self.fast2sms_template_id
            
            headers = {
                "authorization": self.fast2sms_api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Fast2SMS error: {e}")
            return False
    
    def store_otp(self, phone: str, otp: str) -> None:
        otp_storage[phone] = {
            "otp": otp,
            "expiry": time.time() + 300,
            "attempts": 0
        }
    
    def verify_otp(self, phone: str, otp: str) -> bool:
        if phone not in otp_storage:
            return False
        
        stored = otp_storage[phone]
        if time.time() > stored["expiry"]:
            del otp_storage[phone]
            return False
        if stored["attempts"] >= 3:
            del otp_storage[phone]
            return False
        if stored["otp"] == otp:
            del otp_storage[phone]
            return True
        
        stored["attempts"] += 1
        return False
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            return None

auth_service = AuthService()