
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, List, Optional

from functionalities.base import Base

class Contact(Base):
    __tablename__ = 'user_management.contacts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    title = Column(String(100), nullable=True)
    is_blocked = Column(Boolean, default=False)
    is_whitelisted = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    contact_count = Column(Integer, default=0)  # Number of interactions
    last_contact_at = Column(DateTime, nullable=True)
    last_contact_type = Column(String(20), nullable=True)  # 'call', 'text', 'email'
    spam_score = Column(Float, default=0.0)  # AI-calculated spam likelihood
    trust_score = Column(Float, default=50.0)  # Trust rating (0-100)
    priority_level = Column(String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    contact_source = Column(String(50), nullable=True)  # 'manual', 'imported', 'auto_created'
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), nullable=True)
    preferred_contact_method = Column(String(20), default='call')  # 'call', 'text', 'email'
    do_not_disturb_start = Column(String(5), nullable=True)  # HH:MM format
    do_not_disturb_end = Column(String(5), nullable=True)  # HH:MM format
    conctact_metadata = Column(JSON, nullable=True)  # Additional contact metadata
    is_deleted = Column(Boolean, default=False)  # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    notes_rel = relationship("ContactNote", back_populates="contact", cascade="all, delete-orphan")
    groups_rel = relationship("ContactGroupMember", back_populates="contact", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_contacts_user_phone', 'user_id', 'phone_number'),
        Index('idx_contacts_user_email', 'user_id', 'email'),
        Index('idx_contacts_user_name', 'user_id', 'name'),
        Index('idx_contacts_blocked', 'user_id', 'is_blocked'),
        Index('idx_contacts_whitelisted', 'user_id', 'is_whitelisted'),
        Index('idx_contacts_favorite', 'user_id', 'is_favorite'),
        Index('idx_contacts_last_contact', 'user_id', 'last_contact_at'),
    )
    
    def to_dict(self) -> Dict:
        """Convert contact to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'phone_number': self.phone_number,
            'email': self.email,
            'company': self.company,
            'title': self.title,
            'is_blocked': self.is_blocked,
            'is_whitelisted': self.is_whitelisted,
            'is_favorite': self.is_favorite,
            'notes': self.notes,
            'tags': self.tags or [],
            'contact_count': self.contact_count or 0,
            'last_contact_at': self.last_contact_at.isoformat() if self.last_contact_at else None,
            'last_contact_type': self.last_contact_type,
            'spam_score': self.spam_score,
            'trust_score': self.trust_score,
            'priority_level': self.priority_level,
            'contact_source': self.contact_source,
            'avatar_url': self.avatar_url,
            'timezone': self.timezone,
            'preferred_contact_method': self.preferred_contact_method,
            'do_not_disturb_start': self.do_not_disturb_start,
            'do_not_disturb_end': self.do_not_disturb_end,
            'contact_metadata': self.contact_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_display_name(self) -> str:
        """Get the best display name for the contact"""
        if self.name and self.name.strip():
            return self.name.strip()
        elif self.company and self.company.strip():
            return self.company.strip()
        else:
            return self.phone_number or self.email or "Unknown Contact"
    
    def is_in_do_not_disturb(self) -> bool:
        """Check if current time is within do not disturb hours"""
        if not self.do_not_disturb_start or not self.do_not_disturb_end:
            return False
        
        try:
            from datetime import time
            now = datetime.now().time()
            start_time = time(*map(int, self.do_not_disturb_start.split(':')))
            end_time = time(*map(int, self.do_not_disturb_end.split(':')))
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # Crosses midnight
                return now >= start_time or now <= end_time
        except:
            return False
    
    def update_interaction_stats(self, interaction_type: str = 'call'):
        """Update contact interaction statistics"""
        self.contact_count = (self.contact_count or 0) + 1
        self.last_contact_at = datetime.now()
        self.last_contact_type = interaction_type
        self.updated_at = datetime.now()

class ContactNote(Base):
    __tablename__ = 'contact_notes'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    note_text = Column(Text, nullable=False)
    note_type = Column(String(50), default='general')  # 'general', 'call_summary', 'reminder', 'warning'
    is_important = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)  # Private notes not shared with AI
    reminder_date = Column(DateTime, nullable=True)
    tags = Column(JSON, nullable=True)
    group_metadata = Column(JSON, nullable=True)
    created_by = Column(String(50), default='user')  # 'user', 'ai', 'system'
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    contact = relationship("Contact", back_populates="notes_rel")
    
    def to_dict(self) -> Dict:
        """Convert note to dictionary"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'note_text': self.note_text,
            'note_type': self.note_type,
            'is_important': self.is_important,
            'is_private': self.is_private,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'tags': self.tags or [],
            'group_metadata': self.group_metadata or {},
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContactGroup(Base):
    __tablename__ = 'contact_groups'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default='#007bff')  # Hex color code
    is_smart_group = Column(Boolean, default=False)  # Auto-populated based on rules
    smart_rules = Column(JSON, nullable=True)  # Rules for smart groups
    notification_settings = Column(JSON, nullable=True)
    member_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    members = relationship("ContactGroupMember", back_populates="group", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict:
        """Convert group to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'is_smart_group': self.is_smart_group,
            'smart_rules': self.smart_rules or {},
            'notification_settings': self.notification_settings or {},
            'member_metadata': self.member_metadata or {},
            'member_count': len(self.members) if self.members else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContactGroupMember(Base):
    __tablename__ = 'contact_group_members'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('contact_groups.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    added_at = Column(DateTime, server_default=func.now())
    added_by = Column(String(50), default='user')  # 'user', 'auto', 'import'
    
    # Relationships
    group = relationship("ContactGroup", back_populates="members")
    contact = relationship("Contact", back_populates="groups_rel")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_unique_group_contact', 'group_id', 'contact_id', unique=True),
    )
    
    def to_dict(self) -> Dict:
        """Convert membership to dictionary"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'contact_id': self.contact_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'added_by': self.added_by
        }


class ContactInteraction(Base):
    __tablename__ = 'contact_interactions'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    interaction_type = Column(String(20), nullable=False)  # 'call', 'text', 'email', 'meeting'
    direction = Column(String(10), nullable=False)  # 'inbound', 'outbound'
    duration_seconds = Column(Integer, nullable=True)  # For calls
    status = Column(String(20), nullable=True)  # 'completed', 'missed', 'declined', 'busy'
    summary = Column(Text, nullable=True)  # AI-generated summary
    sentiment = Column(String(20), nullable=True)  # 'positive', 'neutral', 'negative'
    importance_score = Column(Float, default=0.0)  # AI-calculated importance (0-1)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    tags = Column(JSON, nullable=True)
    interaction_metadata = Column(JSON, nullable=True)  # Additional interaction data
    external_id = Column(String(100), nullable=True)  # ID from external system (Twilio, etc.)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_interactions_contact', 'contact_id'),
        Index('idx_interactions_user', 'user_id'),
        Index('idx_interactions_type', 'interaction_type'),
        Index('idx_interactions_date', 'created_at'),
        Index('idx_interactions_follow_up', 'follow_up_required', 'follow_up_date'),
    )
    
    def to_dict(self) -> Dict:
        """Convert interaction to dictionary"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'user_id': self.user_id,
            'interaction_type': self.interaction_type,
            'direction': self.direction,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'summary': self.summary,
            'sentiment': self.sentiment,
            'importance_score': self.importance_score,
            'follow_up_required': self.follow_up_required,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'tags': self.tags or [],
            'interaction_metadata': self.interaction_metadata or {},
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_duration_display(self) -> str:
        """Get human-readable duration"""
        if not self.duration_seconds:
            return "N/A"
        
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

class ContactPreference(Base):
    __tablename__ = 'contact_preferences'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    preference_type = Column(String(50), nullable=False)  # 'communication', 'notification', 'ai_behavior'
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        Index('idx_unique_contact_preference', 'contact_id', 'preference_type', 'preference_key', unique=True),
    )
    
    def to_dict(self) -> Dict:
        """Convert preference to dictionary"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'preference_type': self.preference_type,
            'preference_key': self.preference_key,
            'preference_value': self.preference_value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContactRelationship(Base):
    __tablename__ = 'contact_relationships'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    related_contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # 'colleague', 'family', 'friend', 'business'
    relationship_strength = Column(Float, default=0.5)  # 0-1 scale
    is_mutual = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    contact = relationship("Contact", foreign_keys=[contact_id])
    related_contact = relationship("Contact", foreign_keys=[related_contact_id])
    
    def to_dict(self) -> Dict:
        """Convert relationship to dictionary"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'related_contact_id': self.related_contact_id,
            'relationship_type': self.relationship_type,
            'relationship_strength': self.relationship_strength,
            'is_mutual': self.is_mutual,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



class ContactUtils:
    """Utility functions for contact operations"""
    
    @staticmethod
    def normalize_phone_number(phone_number: str) -> str:
        """Normalize phone number for consistent storage and comparison"""
        if not phone_number:
            return ""
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Handle US numbers
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif digits_only.startswith('1') and len(digits_only) > 11:
            return f"+{digits_only}"
        else:
            # For international numbers, assume they're already properly formatted
            return f"+{digits_only}" if not phone_number.startswith('+') else phone_number
    
    @staticmethod
    def format_phone_display(phone_number: str) -> str:
        """Format phone number for display"""
        if not phone_number:
            return ""
        
        # Remove + and country code for US numbers
        digits = ''.join(filter(str.isdigit, phone_number))
        
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]  # Remove US country code
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            return phone_number  # Return original for international numbers
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return True  # Empty email is valid (optional field)
        
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def calculate_contact_similarity(contact1: Contact, contact2: Contact) -> float:
        """Calculate similarity score between two contacts (0-1)"""
        score = 0.0
        factors = 0
        
        # Phone number similarity (highest weight)
        if contact1.phone_number and contact2.phone_number:
            phone1 = ContactUtils.normalize_phone_number(contact1.phone_number)
            phone2 = ContactUtils.normalize_phone_number(contact2.phone_number)
            if phone1 == phone2:
                score += 0.4
            factors += 0.4
        
        # Email similarity
        if contact1.email and contact2.email:
            if contact1.email.lower() == contact2.email.lower():
                score += 0.3
            factors += 0.3
        
        # Name similarity
        if contact1.name and contact2.name:
            name_similarity = ContactUtils._calculate_string_similarity(
                contact1.name.lower(), contact2.name.lower()
            )
            score += name_similarity * 0.2
            factors += 0.2
        
        # Company similarity
        if contact1.company and contact2.company:
            company_similarity = ContactUtils._calculate_string_similarity(
                contact1.company.lower(), contact2.company.lower()
            )
            score += company_similarity * 0.1
            factors += 0.1
        
        return score / factors if factors > 0 else 0.0
    
    @staticmethod
    def _calculate_string_similarity(str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Levenshtein distance"""
        if str1 == str2:
            return 1.0
        
        if not str1 or not str2:
            return 0.0
        
        # Simple implementation of Levenshtein distance
        len1, len2 = len(str1), len(str2)
        if len1 > len2:
            str1, str2 = str2, str1
            len1, len2 = len2, len1
        
        current_row = list(range(len1 + 1))
        for i in range(1, len2 + 1):
            previous_row, current_row = current_row, [i] + [0] * len1
            for j in range(1, len1 + 1):
                add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
                if str1[j - 1] != str2[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)
        
        max_len = max(len(str1), len(str2))
        return 1.0 - (current_row[len1] / max_len)
    
    @staticmethod
    def generate_contact_avatar_url(contact: Contact) -> str:
        """Generate avatar URL for contact"""
        if contact.avatar_url:
            return contact.avatar_url
        
        # Generate a placeholder avatar based on initials
        initials = ''.join([part[0].upper() for part in contact.name.split() if part])[:2]
        return f"https://via.placeholder.com/150?text={initials}"       
