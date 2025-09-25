from dataclasses import dataclass
from typing import Optional, Dict, Any
from api.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: Optional[int]
    email: str
    password_hash: str
    phone_number: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False
    phone_verified: bool = False
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None

@dataclass
class UserSettings:
    id: Optional[int]
    user_id: int
    sms_forwarding_number: Optional[str] = None
    call_forwarding_number: Optional[str] = None
    ai_mode_enabled: bool = True
    ai_mode_expires_at: Optional[str] = None
    spam_filtering_enabled: bool = True
    recording_enabled: bool = False
    transcript_enabled: bool = False
    voice_cloning_enabled: bool = False
    timezone: str = 'UTC'
    language_code: str = 'en'

class UsersRepository(BaseRepository):
    """Repository for user management operations"""

    def __init__(self, database_url: Optional[str] = None, queries_config: Optional[Dict[str, Any]] = None):
        # Fallbacks to tolerate legacy call-sites
        if database_url is None or queries_config is None:
            try:
                # Try Flask app config first
                from flask import current_app
                cfg = current_app.config.get("APP_CONFIG") if current_app else None
                if database_url is None and cfg:
                    database_url = getattr(cfg, 'database_url', None)
                if queries_config is None and cfg:
                    queries_config = getattr(cfg, 'queries', None)
            except Exception:
                pass
            
            if (database_url is None or queries_config is None):
                try:
                    # Last resort: load directly from disk/env
                    from api.utils.config import Config
                    _cfg = Config.load()
                    database_url = database_url or _cfg.database_url
                    queries_config = queries_config or _cfg.queries
                except Exception:
                    # Leave as None; BaseRepository will raise a clear error later
                    pass

        super().__init__(database_url)
        self.queries = queries_config or {}
    
    def create_user(self, email: str, password_hash: str, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            sql = self.queries["users"]["create"]
            rows = self.execute(sql, [email, password_hash, phone_number])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            sql = self.queries["users"]["get_by_id"]
            rows = self.execute(sql, [user_id])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (for general use)"""
        try:
            sql = self.queries["users"]["get_by_email"]
            rows = self.execute(sql, [email])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_email_for_login(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email for login (only active users)"""
        try:
            sql = self.queries["users"]["get_by_email_for_login"]
            rows = self.execute(sql, [email])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error getting user by email for login: {e}")
            return None
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        try:
            sql = self.queries["users"]["get_by_phone"]
            rows = self.execute(sql, [phone_number])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error getting user by phone: {e}")
            return None
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            sql = self.queries["users"]["update_last_login"]
            self.execute(sql, [user_id])
            return True
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            return False
    
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user's password"""
        try:
            sql = self.queries["users"]["update_password"]
            self.execute(sql, [user_id, password_hash])
            return True
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False
    
    def update_profile(self, user_id: int, email: str, phone_number: Optional[str]) -> bool:
        """Update user profile information"""
        try:
            sql = self.queries["users"]["update_profile"]
            self.execute(sql, [user_id, email, phone_number])
            return True
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False
    
    def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified"""
        try:
            sql = self.queries["users"]["verify_email"]
            self.execute(sql, [user_id])
            return True
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False
    
    def verify_phone(self, user_id: int) -> bool:
        """Mark user's phone as verified"""
        try:
            sql = self.queries["users"]["verify_phone"]
            self.execute(sql, [user_id])
            return True
        except Exception as e:
            logger.error(f"Error verifying phone: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        try:
            sql = self.queries["users"]["deactivate"]
            self.execute(sql, [user_id])
            return True
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def activate_user(self, user_id: int) -> bool:
        """Activate a user account"""
        try:
            sql = self.queries["users"]["activate"]
            self.execute(sql, [user_id])
            return True
        except Exception as e:
            logger.error(f"Error activating user: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user account"""
        try:
            sql = self.queries["users"]["delete"]
            self.execute(sql, [user_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def check_email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        try:
            sql = self.queries["users"]["check_email_exists"]
            rows = self.execute(sql, [email])
            return rows[0][0] > 0 if rows else False
        except Exception as e:
            logger.error(f"Error checking email existence: {e}")
            return False
    
    def check_phone_exists(self, phone_number: str) -> bool:
        """Check if phone number already exists"""
        try:
            sql = self.queries["users"]["check_phone_exists"]
            rows = self.execute(sql, [phone_number])
            return rows[0][0] > 0 if rows else False
        except Exception as e:
            logger.error(f"Error checking phone existence: {e}")
            return False
    
    # User Settings methods
    def create_user_settings(self, user_id: int, **settings) -> Optional[Dict[str, Any]]:
        """Create default user settings"""
        try:
            sql = self.queries["user_settings"]["create"]
            rows = self.execute(sql, [
                user_id,
                settings.get('sms_forwarding_number'),
                settings.get('call_forwarding_number'),
                settings.get('ai_mode_enabled', True),
                settings.get('spam_filtering_enabled', True),
                settings.get('recording_enabled', False),
                settings.get('transcript_enabled', False),
                settings.get('voice_cloning_enabled', False),
                settings.get('timezone', 'UTC'),
                settings.get('language_code', 'en')
            ])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error creating user settings: {e}")
            raise
    
    def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        try:
            sql = self.queries["user_settings"]["get_by_user"]
            rows = self.execute(sql, [user_id])
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return None
