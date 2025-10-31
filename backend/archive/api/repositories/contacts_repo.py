
from datetime import datetime

from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, desc, func
from api.repositories.base import BaseRepository
try:
    from functionalities.contacts import Contact, ContactGroup, ContactNote  # type: ignore
except Exception:  # archived/unavailable
    Contact = None  # type: ignore
    ContactGroup = None  # type: ignore
    ContactNote = None  # type: ignore

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_, or_, desc, func, text
from api.repositories.base import BaseRepository
from functionalities.contacts import Contact, ContactGroup, ContactNote
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ContactsRepository(BaseRepository):
    """Repository for contact-related operations"""
    
    def __init__(self, database_url: str, queries_config: Dict):
        super().__init__(database_url, queries_config)
        self.model_class = Contact
        if self.model_class is None:
            logger.warning("Contacts functionality archived; repository is disabled.")

    def _disabled(self) -> bool:
        return self.model_class is None
    
    def create_contact(self, contact_data: Dict) -> Optional[int]:
        """Create a new contact"""
        if self._disabled():
            logger.info("create_contact skipped: Contacts repository disabled")
            return None
        try:
            with self.get_session() as session:
                contact = Contact(
                    user_id=contact_data['user_id'],
                    name=contact_data['name'],
                    phone_number=contact_data['phone_number'],
                    email=contact_data.get('email'),
                    company=contact_data.get('company'),
                    title=contact_data.get('title'),
                    is_blocked=contact_data.get('is_blocked', False),
                    is_whitelisted=contact_data.get('is_whitelisted', False),
                    is_favorite=contact_data.get('is_favorite', False),
                    notes=contact_data.get('notes'),
                    tags=contact_data.get('tags', []),
                    conctact_metadata=contact_data.get('metadata', {})
                )
                
                session.add(contact)
                session.commit()
                session.refresh(contact)
                
                logger.info(f"Created contact {contact.id} for user {contact_data['user_id']}")
                return contact.id
                
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None
    
    def update_contact(self, contact_id: int, update_data: Dict) -> bool:
        """Update an existing contact"""
        if self._disabled():
            logger.info("update_contact skipped: Contacts repository disabled")
            return False
        try:
            with self.get_session() as session:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                
                if not contact:
                    logger.warning(f"Contact {contact_id} not found for update")
                    return False
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(contact, key):
                        setattr(contact, key, value)
                
                contact.updated_at = datetime.now()
                session.commit()
                logger.info(f"Updated contact {contact_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return False
    
    def get_contact(self, contact_id: int, user_id: int = None) -> Optional[Dict]:
        """Get a specific contact by ID"""
        if self._disabled():
            logger.info("get_contact skipped: Contacts repository disabled")
            return None
        try:
            with self.get_session() as session:
                query = session.query(Contact).filter(Contact.id == contact_id)
                
                if user_id:
                    query = query.filter(Contact.user_id == user_id)
                
                contact = query.first()
                
                if contact:
                    return contact.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            return None
    
    def get_by_phone(self, user_id: int, phone_number: str) -> Optional[Dict]:
        """Get contact by phone number"""
        if self._disabled():
            logger.info("get_by_phone skipped: Contacts repository disabled")
            return None
        try:
            with self.get_session() as session:
                # Clean phone number for comparison
                clean_phone = self._clean_phone_number(phone_number)
                
                contact = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        or_(
                            Contact.phone_number == phone_number,
                            Contact.phone_number == clean_phone,
                            func.replace(func.replace(func.replace(Contact.phone_number, '-', ''), ' ', ''), '(', '').like(f"%{clean_phone}%")
                        )
                    )
                ).first()
                
                if contact:
                    return contact.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error getting contact by phone {phone_number}: {e}")
            return None
    
    def get_contact_by_phone(self, phone_number: str, user_id: int) -> Optional[Dict]:
        """Alternative method name for compatibility"""
        return self.get_by_phone(user_id, phone_number)
    
    def get_contacts(self, user_id: int, filters: Dict = None) -> List[Dict]:
        """Get all contacts for a user with optional filters"""
        if self._disabled():
            logger.info("get_contacts skipped: Contacts repository disabled")
            return []
        try:
            with self.get_session() as session:
                query = session.query(Contact).filter(Contact.user_id == user_id)
                
                if filters:
                    # Name search
                    if filters.get('search'):
                        search_term = f"%{filters['search']}%"
                        query = query.filter(
                            or_(
                                Contact.name.ilike(search_term),
                                Contact.phone_number.like(search_term),
                                Contact.email.ilike(search_term),
                                Contact.company.ilike(search_term)
                            )
                        )
                    
                    # Blocked filter
                    if filters.get('is_blocked') is not None:
                        query = query.filter(Contact.is_blocked == filters['is_blocked'])
                    
                    # Whitelisted filter
                    if filters.get('is_whitelisted') is not None:
                        query = query.filter(Contact.is_whitelisted == filters['is_whitelisted'])
                    
                    # Favorites filter
                    if filters.get('is_favorite') is not None:
                        query = query.filter(Contact.is_favorite == filters['is_favorite'])
                    
                    # Tag filter
                    if filters.get('tag'):
                        query = query.filter(Contact.tags.contains([filters['tag']]))
                    
                    # Company filter
                    if filters.get('company'):
                        query = query.filter(Contact.company.ilike(f"%{filters['company']}%"))
                
                # Ordering
                order_by = filters.get('order_by', 'name') if filters else 'name'
                if order_by == 'name':
                    query = query.order_by(Contact.name)
                elif order_by == 'created_at':
                    query = query.order_by(desc(Contact.created_at))
                elif order_by == 'updated_at':
                    query = query.order_by(desc(Contact.updated_at))
                elif order_by == 'last_contact':
                    query = query.order_by(desc(Contact.last_contact_at))
                
                # Pagination
                limit = filters.get('limit', 100) if filters else 100
                offset = filters.get('offset', 0) if filters else 0
                
                contacts = query.offset(offset).limit(limit).all()
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error getting contacts for user {user_id}: {e}")
            return []
    
    def search_contacts(self, user_id: int, search_term: str, limit: int = 50) -> List[Dict]:
        """Search contacts by name, phone, email, or company"""
        try:
            with self.get_session() as session:
                search_pattern = f"%{search_term}%"
                
                contacts = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        or_(
                            Contact.name.ilike(search_pattern),
                            Contact.phone_number.like(search_pattern),
                            Contact.email.ilike(search_pattern),
                            Contact.company.ilike(search_pattern)
                        )
                    )
                ).order_by(Contact.name).limit(limit).all()
                
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    def get_blocked_contacts(self, user_id: int) -> List[Dict]:
        """Get all blocked contacts"""
        try:
            with self.get_session() as session:
                contacts = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        Contact.is_blocked == True
                    )
                ).order_by(Contact.name).all()
                
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error getting blocked contacts: {e}")
            return []
    
    def get_whitelisted_contacts(self, user_id: int) -> List[Dict]:
        """Get all whitelisted contacts"""
        try:
            with self.get_session() as session:
                contacts = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        Contact.is_whitelisted == True
                    )
                ).order_by(Contact.name).all()
                
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error getting whitelisted contacts: {e}")
            return []
    
    def get_favorite_contacts(self, user_id: int) -> List[Dict]:
        """Get all favorite contacts"""
        try:
            with self.get_session() as session:
                contacts = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        Contact.is_favorite == True
                    )
                ).order_by(Contact.name).all()
                
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error getting favorite contacts: {e}")
            return []
    
    def block_contact(self, contact_id: int, user_id: int) -> bool:
        """Block a contact"""
        return self.update_contact(contact_id, {'is_blocked': True})
    
    def unblock_contact(self, contact_id: int, user_id: int) -> bool:
        """Unblock a contact"""
        return self.update_contact(contact_id, {'is_blocked': False})
    
    def whitelist_contact(self, contact_id: int, user_id: int) -> bool:
        """Add contact to whitelist"""
        return self.update_contact(contact_id, {'is_whitelisted': True})
    
    def remove_from_whitelist(self, contact_id: int, user_id: int) -> bool:
        """Remove contact from whitelist"""
        return self.update_contact(contact_id, {'is_whitelisted': False})
    
    def add_to_favorites(self, contact_id: int, user_id: int) -> bool:
        """Add contact to favorites"""
        return self.update_contact(contact_id, {'is_favorite': True})
    
    def remove_from_favorites(self, contact_id: int, user_id: int) -> bool:
        """Remove contact from favorites"""
        return self.update_contact(contact_id, {'is_favorite': False})
    
    def delete_contact(self, contact_id: int, user_id: int) -> bool:
        """Delete a contact"""
        try:
            with self.get_session() as session:
                contact = session.query(Contact).filter(
                    and_(Contact.id == contact_id, Contact.user_id == user_id)
                ).first()
                
                if contact:
                    session.delete(contact)
                    session.commit()
                    logger.info(f"Deleted contact {contact_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error deleting contact {contact_id}: {e}")
            return False
    
    def add_contact_note(self, contact_id: int, note_data: Dict) -> Optional[int]:
        """Add a note to a contact"""
        try:
            with self.get_session() as session:
                note = ContactNote(
                    contact_id=contact_id,
                    note_text=note_data['note_text'],
                    note_type=note_data.get('note_type', 'general'),
                    is_important=note_data.get('is_important', False),
                    group_metadata=note_data.get('metadata', {})
                )
                
                session.add(note)
                session.commit()
                session.refresh(note)
                
                logger.info(f"Added note {note.id} to contact {contact_id}")
                return note.id
                
        except Exception as e:
            logger.error(f"Error adding note to contact {contact_id}: {e}")
            return None
    
    def get_contact_notes(self, contact_id: int) -> List[Dict]:
        """Get all notes for a contact"""
        try:
            with self.get_session() as session:
                notes = session.query(ContactNote).filter(
                    ContactNote.contact_id == contact_id
                ).order_by(desc(ContactNote.created_at)).all()
                
                return [note.to_dict() for note in notes]
                
        except Exception as e:
            logger.error(f"Error getting notes for contact {contact_id}: {e}")
            return []
    
    def update_last_contact(self, contact_id: int, contact_type: str = 'call') -> bool:
        """Update the last contact timestamp"""
        try:
            with self.get_session() as session:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                
                if contact:
                    contact.last_contact_at = datetime.now()
                    contact.last_contact_type = contact_type
                    contact.contact_count = (contact.contact_count or 0) + 1
                    session.commit()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating last contact for {contact_id}: {e}")
            return False
    
    def get_contact_statistics(self, user_id: int) -> Dict:
        """Get contact statistics for a user"""
        try:
            with self.get_session() as session:
                total_contacts = session.query(Contact).filter(Contact.user_id == user_id).count()
                blocked_contacts = session.query(Contact).filter(
                    and_(Contact.user_id == user_id, Contact.is_blocked == True)
                ).count()
                whitelisted_contacts = session.query(Contact).filter(
                    and_(Contact.user_id == user_id, Contact.is_whitelisted == True)
                ).count()
                favorite_contacts = session.query(Contact).filter(
                    and_(Contact.user_id == user_id, Contact.is_favorite == True)
                ).count()
                
                # Recent contacts (contacted in last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_contacts = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        Contact.last_contact_at >= thirty_days_ago
                    )
                ).count()
                
                return {
                    'total_contacts': total_contacts,
                    'blocked_contacts': blocked_contacts,
                    'whitelisted_contacts': whitelisted_contacts,
                    'favorite_contacts': favorite_contacts,
                    'recent_contacts': recent_contacts
                }
                
        except Exception as e:
            logger.error(f"Error getting contact statistics: {e}")
            return {}
    
    def get_contacts_by_tag(self, user_id: int, tag: str) -> List[Dict]:
        """Get contacts by tag"""
        try:
            with self.get_session() as session:
                contacts = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        Contact.tags.contains([tag])
                    )
                ).order_by(Contact.name).all()
                
                return [contact.to_dict() for contact in contacts]
                
        except Exception as e:
            logger.error(f"Error getting contacts by tag {tag}: {e}")
            return []
    
    def get_all_tags(self, user_id: int) -> List[str]:
        """Get all unique tags used by user's contacts"""
        try:
            with self.get_session() as session:
                contacts = session.query(Contact.tags).filter(
                    and_(Contact.user_id == user_id, Contact.tags.isnot(None))
                ).all()
                
                all_tags = set()
                for contact in contacts:
                    if contact.tags:
                        all_tags.update(contact.tags)
                
                return sorted(list(all_tags))
                
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            return []
    
    def merge_contacts(self, primary_contact_id: int, secondary_contact_id: int, user_id: int) -> bool:
        """Merge two contacts, keeping the primary and merging data from secondary"""
        try:
            with self.get_session() as session:
                primary = session.query(Contact).filter(
                    and_(Contact.id == primary_contact_id, Contact.user_id == user_id)
                ).first()
                secondary = session.query(Contact).filter(
                    and_(Contact.id == secondary_contact_id, Contact.user_id == user_id)
                ).first()
                
                if not primary or not secondary:
                    return False
                
                # Merge data from secondary to primary
                if not primary.email and secondary.email:
                    primary.email = secondary.email
                if not primary.company and secondary.company:
                    primary.company = secondary.company
                if not primary.title and secondary.title:
                    primary.title = secondary.title
                
                # Merge tags
                if secondary.tags:
                    primary_tags = set(primary.tags or [])
                    secondary_tags = set(secondary.tags)
                    primary.tags = list(primary_tags.union(secondary_tags))
                
                # Merge notes
                if primary.notes and secondary.notes:
                    primary.notes = f"{primary.notes}\n\n--- Merged from {secondary.name} ---\n{secondary.notes}"
                elif secondary.notes:
                    primary.notes = secondary.notes
                
                # Update contact count and last contact
                primary.contact_count = (primary.contact_count or 0) + (secondary.contact_count or 0)
                if secondary.last_contact_at and (not primary.last_contact_at or secondary.last_contact_at > primary.last_contact_at):
                    primary.last_contact_at = secondary.last_contact_at
                    primary.last_contact_type = secondary.last_contact_type
                
                # Delete secondary contact
                session.delete(secondary)
                session.commit()
                
                logger.info(f"Merged contact {secondary_contact_id} into {primary_contact_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error merging contacts: {e}")
            return False
    
    def bulk_update_contacts(self, user_id: int, contact_ids: List[int], update_data: Dict) -> int:
        """Bulk update multiple contacts"""
        try:
            with self.get_session() as session:
                updated_count = session.query(Contact).filter(
                    and_(
                        Contact.user_id == user_id,
                        Contact.id.in_(contact_ids)
                    )
                ).update(update_data, synchronize_session=False)
                
                session.commit()
                logger.info(f"Bulk updated {updated_count} contacts")
                return updated_count
                
        except Exception as e:
            logger.error(f"Error bulk updating contacts: {e}")
            return 0
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean phone number for comparison"""
        if not phone_number:
            return ""
        
        # Remove common formatting characters
        cleaned = phone_number.replace('-', '').replace(' ', '').replace('(', '').replace(')', '').replace('+', '')
        
        # Remove country code if present (assuming US numbers)
        if cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = cleaned[1:]
        
        return cleaned
    
    def find_duplicate_contacts(self, user_id: int) -> List[Dict]:
        """Find potential duplicate contacts based on phone number or email"""
        try:
            with self.get_session() as session:
                contacts = session.query(Contact).filter(Contact.user_id == user_id).all()
                
                duplicates = []
                phone_map = {}
                email_map = {}
                
                for contact in contacts:
                    # Check phone duplicates
                    if contact.phone_number:
                        clean_phone = self._clean_phone_number(contact.phone_number)
                        if clean_phone in phone_map:
                            duplicates.append({
                                'type': 'phone',
                                'contacts': [phone_map[clean_phone].to_dict(), contact.to_dict()],
                                'matching_field': clean_phone
                            })
                        else:
                            phone_map[clean_phone] = contact
                    
                    # Check email duplicates
                    if contact.email:
                        email_lower = contact.email.lower()
                        if email_lower in email_map:
                            duplicates.append({
                                'type': 'email',
                                'contacts': [email_map[email_lower].to_dict(), contact.to_dict()],
                                'matching_field': email_lower
                            })
                        else:
                            email_map[email_lower] = contact
                
                return duplicates
                
        except Exception as e:
            logger.error(f"Error finding duplicate contacts: {e}")
            return []
