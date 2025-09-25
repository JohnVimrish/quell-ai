"""
Security utilities for password hashing and verification
"""
import hashlib
import secrets
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class PasswordManager:
    """Secure password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using PBKDF2 with a random salt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password in format: salt:hash
        """
        try:
            # Generate a random salt
            salt = secrets.token_hex(32)  # 64 character hex string
            
            # Hash the password with PBKDF2
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000  # 100,000 iterations
            )
            
            # Return salt:hash format
            return f"{salt}:{password_hash.hex()}"
            
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise ValueError("Failed to hash password")
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored hash in format salt:hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # Split salt and hash
            if ':' not in hashed_password:
                logger.warning("Invalid hash format")
                return False
                
            salt, stored_hash = hashed_password.split(':', 1)
            
            # Hash the provided password with the same salt
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000  # Same number of iterations
            )
            
            # Compare hashes
            return secrets.compare_digest(password_hash.hex(), stored_hash)
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token
        
        Args:
            length: Length of token in bytes (default 32)
            
        Returns:
            Hex-encoded random token
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        # Check for common weak passwords
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            return False, "Password is too common, please choose a stronger password"
        
        return True, "Password is valid"
