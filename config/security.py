"""
Security Configuration Module
Handles authentication, authorization, and security settings
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import bcrypt


class SecurityConfig:
    def __init__(self):
        # JWT Configuration
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours

        # Admin Key Configuration
        self.ADMIN_KEY_HASH = os.getenv("ADMIN_KEY_HASH", self._generate_default_admin_hash())

        # Password Hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Rate Limiting
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour

        # Security Headers
        self.SECURITY_HEADERS = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'"
        }

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)

    def _generate_default_admin_hash(self) -> str:
        """Generate default admin key hash"""
        default_key = "jee-admin-2025-secure"
        return bcrypt.hashpw(default_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)

    def verify_admin_key(self, admin_key: str) -> bool:
        """Verify admin key"""
        try:
            return bcrypt.checkpw(admin_key.encode('utf-8'), self.ADMIN_KEY_HASH.encode('utf-8'))
        except Exception:
            return False

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.JWT_EXPIRATION_MINUTES)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.JWT_SECRET_KEY, algorithm=self.JWT_ALGORITHM)
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=[self.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return self.SECURITY_HEADERS


# Global security instance
security = SecurityConfig()
