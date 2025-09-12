from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class CallAnalytics(Base):
    __tablename__ = 'call_analytics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    total_calls = Column(Integer, default=0)
    ai_handled_calls = Column(Integer, default=0)
    user_handled_calls = Column(Integer, default=0)
    missed_calls = Column(Integer, default=0)
    spam_calls_blocked = Column(Integer, default=0)
    important_calls = Column(Integer, default=0)
    average_call_duration = Column(Float, default=0.0)
    ai_success_rate = Column(Float, default=0.0)  # Percentage of successful AI interactions
    escalation_rate = Column(Float, default=0.0)  # Percentage of calls escalated to user
    caller_satisfaction_avg = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class WeeklyReport(Base):
    __tablename__ = 'weekly_reports'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    
    # Call Statistics
    total_calls = Column(Integer, default=0)
    ai_handled_calls = Column(Integer, default=0)
    user_handled_calls = Column(Integer, default=0)
    missed_calls = Column(Integer, default=0)
    spam_calls_blocked = Column(Integer, default=0)
    important_calls = Column(Integer, default=0)
    
    # Text Statistics
    total_texts = Column(Integer, default=0)
    ai_handled_texts = Column(Integer, default=0)
    user_handled_texts = Column(Integer, default=0)
    spam_texts_blocked = Column(Integer, default=0)
    
    # Performance Metrics
    ai_success_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    caller_satisfaction_avg = Column(Float, nullable=True)
    
    # Insights and Patterns
    peak_call_hours = Column(JSON, nullable=True)  # Hour-by-hour breakdown
