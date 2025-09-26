from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class TextConversation(Base):
    __tablename__ = 'text_conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)
    phone_number = Column(String(20), nullable=False)
    contact_name = Column(String(100), nullable=True)
    is_group = Column(Boolean, default=False)
    ai_active = Column(Boolean, default=False)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    messages = relationship("TextMessage", back_populates="conversation")
    contact = relationship("Contact")

class TextMessage(Base):
    __tablename__ = 'text_messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('text_conversations.id'), nullable=False)
    direction = Column(String(10), nullable=False)  # 'inbound', 'outbound'
    sender_number = Column(String(20), nullable=False)
    message_text = Column(Text, nullable=False)
    message_type = Column(String(20), default='text')  # 'text', 'image', 'file', 'location'
    ai_generated = Column(Boolean, default=False)
    spam_score = Column(Integer, default=0)
    category = Column(String(20), default='routine')  # 'important', 'spam', 'routine'
    read_status = Column(Boolean, default=False)
    sentiment_score = Column(Integer, default=0)  # -100 to 100
    urgency_level = Column(String(10), default='normal')  # 'low', 'normal', 'high', 'urgent'
    auto_reply_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    conversation = relationship("TextConversation", back_populates="messages")
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'direction': self.direction,
            'sender_number': self.sender_number,
            'message_text': self.message_text,
            'message_type': self.message_type,
            'ai_generated': self.ai_generated,
            'spam_score': self.spam_score,
            'category': self.category,
            'read_status': self.read_status,
            'sentiment_score': self.sentiment_score,
            'urgency_level': self.urgency_level,
            'auto_reply_sent': self.auto_reply_sent,
            'created_at': self.created_at.isoformat()
        }
