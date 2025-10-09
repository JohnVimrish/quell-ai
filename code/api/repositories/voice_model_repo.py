
from typing import List, Dict, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_, or_, desc
from api.repositories.base import BaseRepository
from functionalities.voice_model import VoiceModel, VoiceSample, VoiceGeneration
import logging

logger = logging.getLogger(__name__)

class VoiceModelRepository(BaseRepository):
    """Repository for voice model operations"""
    
    def __init__(self, database_url: str, queries_config: Dict):
        super().__init__(database_url, queries_config)
        self.model_class = VoiceModel
    
    def create_voice_model(self, user_id: int, model_data: Dict) -> Optional[Dict]:
        """Create a new voice model"""
        try:
            with self.get_session() as session:
                voice_model = VoiceModel(
                    user_id=user_id,
                    model_name=model_data['model_name'],
                    model_path=model_data['model_path'],
                    training_config=model_data.get('training_config'),
                    disclosure_text=model_data.get('disclosure_text')
                )
                
                session.add(voice_model)
                session.commit()
                session.refresh(voice_model)
                
                logger.info(f"Created voice model {voice_model.id} for user {user_id}")
                return voice_model.to_dict()
                
        except Exception as e:
            logger.error(f"Error creating voice model: {e}")
            return None
    
    def get_user_voice_models(self, user_id: int, include_inactive: bool = False) -> List[Dict]:
        """Get all voice models for a user"""
        try:
            with self.get_session() as session:
                query = session.query(VoiceModel).filter(VoiceModel.user_id == user_id)
                
                if not include_inactive:
                    query = query.filter(VoiceModel.is_active == True)
                
                models = query.order_by(desc(VoiceModel.created_at)).all()
                return [model.to_dict() for model in models]
                
        except Exception as e:
            logger.error(f"Error getting user voice models: {e}")
            return []
    
    def get_voice_model(self, model_id: int, user_id: int = None) -> Optional[Dict]:
        """Get a specific voice model by ID"""
        try:
            with self.get_session() as session:
                query = session.query(VoiceModel).filter(VoiceModel.id == model_id)
                
                if user_id:
                    query = query.filter(VoiceModel.user_id == user_id)
                
                model = query.first()
                return model.to_dict() if model else None
                
        except Exception as e:
            logger.error(f"Error getting voice model {model_id}: {e}")
            return None
