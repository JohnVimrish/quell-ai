
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_, or_, desc, func, text
from api.repositories.base import BaseRepository
from functionalities.call import Call, CallParticipant, CallTranscript
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CallsRepository(BaseRepository):
    """Repository for call-related operations"""
    
    def __init__(self, database_url: str, queries_config: Dict):
        super().__init__(database_url, queries_config)
        self.model_class = Call
    
    def create_call(self, call_data: Dict) -> Optional[int]:
        """Create a new call record"""
        try:
            with self.get_session() as session:
                call = Call(
                    user_id=call_data['user_id'],
                    contact_id=call_data.get('contact_id'),
                    phone_number=call_data['phone_number'],
                    direction=call_data['direction'],
                    status=call_data.get('status', 'initiated'),
                    external_call_id=call_data.get('external_call_id'),
                    caller_name=call_data.get('caller_name'),
                    started_at=datetime.fromisoformat(call_data['started_at']) if isinstance(call_data['started_at'], str) else call_data['started_at']
                )
                
                session.add(call)
                session.commit()
                session.refresh(call)
                
                logger.info(f"Created call {call.id} for user {call_data['user_id']}")
                return call.id
                
        except Exception as e:
            logger.error(f"Error creating call: {e}")
            return None
    
    def update_call(self, call_id: int, update_data: Dict) -> bool:
        """Update an existing call"""
        try:
            with self.get_session() as session:
                call = session.query(Call).filter(Call.id == call_id).first()
                
                if not call:
                    logger.warning(f"Call {call_id} not found for update")
                    return False
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(call, key):
                        if key in ['started_at', 'ended_at'] and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        setattr(call, key, value)
                
                session.commit()
                logger.info(f"Updated call {call_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating call {call_id}: {e}")
            return False
    
    def get_call(self, call_id: int, user_id: int = None) -> Optional[Dict]:
        """Get a specific call by ID"""
        try:
            with self.get_session() as session:
                query = session.query(Call).filter(Call.id == call_id)
                
                if user_id:
                    query = query.filter(Call.user_id == user_id)
                
                call = query.first()
                
                if call:
                    return call.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error getting call {call_id}: {e}")
            return None
    
    def get_recent_calls(self, user_id: int, limit: int = 50, include_spam: bool = False) -> List[Dict]:
        """Get recent calls for a user"""
        try:
            with self.get_session() as session:
                query = session.query(Call).filter(Call.user_id == user_id)
                
                if not include_spam:
                    query = query.filter(or_(Call.is_spam == False, Call.is_spam.is_(None)))
                
                calls = query.order_by(desc(Call.started_at)).limit(limit).all()
                return [call.to_dict() for call in calls]
                
        except Exception as e:
            logger.error(f"Error getting recent calls for user {user_id}: {e}")
            return []
    
    def get_calls_by_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get calls within a date range"""
        try:
            with self.get_session() as session:
                calls = session.query(Call).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.started_at >= start_date,
                        Call.started_at <= end_date
                    )
                ).order_by(desc(Call.started_at)).all()
                
                return [call.to_dict() for call in calls]
                
        except Exception as e:
            logger.error(f"Error getting calls by date range: {e}")
            return []
    
    def get_call_statistics(self, user_id: int, days: int = 30) -> Dict:
        """Get call statistics for a user"""
        try:
            with self.get_session() as session:
                start_date = datetime.now() - timedelta(days=days)
                
                # Total calls
                total_calls = session.query(func.count(Call.id)).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.started_at >= start_date
                    )
                ).scalar()
                
                # Incoming vs outgoing
                incoming_calls = session.query(func.count(Call.id)).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.direction == 'incoming',
                        Call.started_at >= start_date
                    )
                ).scalar()
                
                outgoing_calls = session.query(func.count(Call.id)).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.direction == 'outgoing',
                        Call.started_at >= start_date
                    )
                ).scalar()
                
                # Spam calls
                spam_calls = session.query(func.count(Call.id)).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.is_spam == True,
                        Call.started_at >= start_date
                    )
                ).scalar()
                
                # Average call duration
                avg_duration = session.query(func.avg(Call.duration_seconds)).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.duration_seconds.isnot(None),
                        Call.started_at >= start_date
                    )
                ).scalar()
                
                # Missed calls
                missed_calls = session.query(func.count(Call.id)).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.status == 'missed',
                        Call.started_at >= start_date
                    )
                ).scalar()
                
                return {
                    'total_calls': total_calls or 0,
                    'incoming_calls': incoming_calls or 0,
                    'outgoing_calls': outgoing_calls or 0,
                    'spam_calls': spam_calls or 0,
                    'missed_calls': missed_calls or 0,
                    'average_duration_seconds': float(avg_duration) if avg_duration else 0,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting call statistics: {e}")
            return {}
    
    def search_calls(self, user_id: int, search_params: Dict) -> List[Dict]:
        """Search calls with various filters"""
        try:
            with self.get_session() as session:
                query = session.query(Call).filter(Call.user_id == user_id)
                
                # Phone number search
                if search_params.get('phone_number'):
                    query = query.filter(Call.phone_number.like(f"%{search_params['phone_number']}%"))
                
                # Caller name search
                if search_params.get('caller_name'):
                    query = query.filter(Call.caller_name.ilike(f"%{search_params['caller_name']}%"))
                
                # Direction filter
                if search_params.get('direction'):
                    query = query.filter(Call.direction == search_params['direction'])
                
                # Status filter
                if search_params.get('status'):
                    query = query.filter(Call.status == search_params['status'])
                
                # Date range
                if search_params.get('start_date'):
                    start_date = datetime.fromisoformat(search_params['start_date'])
                    query = query.filter(Call.started_at >= start_date)
                
                if search_params.get('end_date'):
                    end_date = datetime.fromisoformat(search_params['end_date'])
                    query = query.filter(Call.started_at <= end_date)
                
                # Duration filter
                if search_params.get('min_duration'):
                    query = query.filter(Call.duration_seconds >= search_params['min_duration'])
                
                if search_params.get('max_duration'):
                    query = query.filter(Call.duration_seconds <= search_params['max_duration'])
                
                # Spam filter
                if search_params.get('include_spam') is False:
                    query = query.filter(or_(Call.is_spam == False, Call.is_spam.is_(None)))
                
                # Limit and order
                limit = search_params.get('limit', 100)
                calls = query.order_by(desc(Call.started_at)).limit(limit).all()
                
                return [call.to_dict() for call in calls]
                
        except Exception as e:
            logger.error(f"Error searching calls: {e}")
            return []
    
    def get_frequent_contacts(self, user_id: int, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get most frequently called contacts"""
        try:
            with self.get_session() as session:
                start_date = datetime.now() - timedelta(days=days)
                
                # Query for frequent phone numbers
                frequent_numbers = session.query(
                    Call.phone_number,
                    Call.caller_name,
                    func.count(Call.id).label('call_count'),
                    func.sum(Call.duration_seconds).label('total_duration')
                ).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.started_at >= start_date,
                        or_(Call.is_spam == False, Call.is_spam.is_(None))
                    )
                ).group_by(
                    Call.phone_number, Call.caller_name
                ).order_by(
                    desc('call_count')
                ).limit(limit).all()
                
                return [
                    {
                        'phone_number': number,
                        'caller_name': name,
                        'call_count': count,
                        'total_duration_seconds': duration or 0
                    }
                    for number, name, count, duration in frequent_numbers
                ]
                
        except Exception as e:
            logger.error(f"Error getting frequent contacts: {e}")
            return []
    
    def mark_as_spam(self, call_id: int, user_id: int) -> bool:
        """Mark a call as spam"""
        try:
            with self.get_session() as session:
                call = session.query(Call).filter(
                    and_(Call.id == call_id, Call.user_id == user_id)
                ).first()
                
                if call:
                    call.is_spam = True
                    session.commit()
                    
                    logger.info(f"Marked call {call_id} as spam for user {user_id}")
                    return True
                else:
                    logger.warning(f"Call {call_id} not found for user {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error marking call {call_id} as spam: {e}")
            return False
            
    
    def unmark_spam(self, call_id: int, user_id: int) -> bool:
        """Remove spam marking from a call"""
        try:
            with self.get_session() as session:
                call = session.query(Call).filter(
                    and_(Call.id == call_id, Call.user_id == user_id)
                ).first()
                
                if call:
                    call.is_spam = False
                    session.commit()
                    logger.info(f"Unmarked call {call_id} as spam")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error unmarking call as spam: {e}")
            return False
    
    def delete_call(self, call_id: int, user_id: int) -> bool:
        """Delete a call record"""
        try:
            with self.get_session() as session:
                call = session.query(Call).filter(
                    and_(Call.id == call_id, Call.user_id == user_id)
                ).first()
                
                if call:
                    session.delete(call)
                    session.commit()
                    logger.info(f"Deleted call {call_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error deleting call: {e}")
            return False
    
    def get_call_by_external_id(self, external_call_id: str) -> Optional[Dict]:
        """Get call by external provider ID (e.g., Twilio CallSid)"""
        try:
            with self.get_session() as session:
                call = session.query(Call).filter(
                    Call.external_call_id == external_call_id
                ).first()
                
                if call:
                    return call.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error getting call by external ID: {e}")
            return None
    
    def add_call_transcript(self, call_id: int, transcript_data: Dict) -> Optional[int]:
        """Add transcript to a call"""
        try:
            with self.get_session() as session:
                transcript = CallTranscript(
                    call_id=call_id,
                    transcript_text=transcript_data['transcript_text'],
                    confidence_score=transcript_data.get('confidence_score'),
                    language=transcript_data.get('language', 'en'),
                    speaker_labels=transcript_data.get('speaker_labels'),
                    timestamps=transcript_data.get('timestamps'),
                    provider=transcript_data.get('provider', 'unknown')
                )
                
                session.add(transcript)
                session.commit()
                session.refresh(transcript)
                
                logger.info(f"Added transcript {transcript.id} to call {call_id}")
                return transcript.id
                
        except Exception as e:
            logger.error(f"Error adding call transcript: {e}")
            return None
    
    def get_call_transcript(self, call_id: int) -> Optional[Dict]:
        """Get transcript for a call"""
        try:
            with self.get_session() as session:
                transcript = session.query(CallTranscript).filter(
                    CallTranscript.call_id == call_id
                ).first()
                
                if transcript:
                    return transcript.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error getting call transcript: {e}")
            return None
    
    def add_call_participant(self, call_id: int, participant_data: Dict) -> Optional[int]:
        """Add participant to a call"""
        try:
            with self.get_session() as session:
                participant = CallParticipant(
                    call_id=call_id,
                    phone_number=participant_data['phone_number'],
                    name=participant_data.get('name'),
                    role=participant_data.get('role', 'participant'),
                    joined_at=datetime.fromisoformat(participant_data['joined_at']) if isinstance(participant_data['joined_at'], str) else participant_data['joined_at'],
                    left_at=datetime.fromisoformat(participant_data['left_at']) if participant_data.get('left_at') and isinstance(participant_data['left_at'], str) else participant_data.get('left_at')
                )
                
                session.add(participant)
                session.commit()
                session.refresh(participant)
                
                logger.info(f"Added participant {participant.id} to call {call_id}")
                return participant.id
                
        except Exception as e:
            logger.error(f"Error adding call participant: {e}")
            return None
    
    def get_call_participants(self, call_id: int) -> List[Dict]:
        """Get all participants for a call"""
        try:
            with self.get_session() as session:
                participants = session.query(CallParticipant).filter(
                    CallParticipant.call_id == call_id
                ).all()
                
                return [participant.to_dict() for participant in participants]
                
        except Exception as e:
            logger.error(f"Error getting call participants: {e}")
            return []
    
    def get_daily_call_summary(self, user_id: int, date: datetime) -> Dict:
        """Get call summary for a specific day"""
        try:
            with self.get_session() as session:
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)
                
                calls = session.query(Call).filter(
                    and_(
                        Call.user_id == user_id,
                        Call.started_at >= start_of_day,
                        Call.started_at < end_of_day
                    )
                ).all()
                
                summary = {
                    'date': date.date().isoformat(),
                    'total_calls': len(calls),
                    'incoming_calls': len([c for c in calls if c.direction == 'incoming']),
                    'outgoing_calls': len([c for c in calls if c.direction == 'outgoing']),
                    'missed_calls': len([c for c in calls if c.status == 'missed']),
                    'spam_calls': len([c for c in calls if c.is_spam]),
                    'total_duration_seconds': sum(c.duration_seconds or 0 for c in calls),
                    'calls': [call.to_dict() for call in calls]
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting daily call summary: {e}")
            return {}