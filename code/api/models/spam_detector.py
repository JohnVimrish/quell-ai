import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import joblib
import re
import phonenumbers
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..models.vector_store import SpamPattern, MLModelMetrics
from ..utils.config import Config

logger = logging.getLogger(__name__)

class AdvancedSpamDetector:
    """
    Multi-layered spam detection system using ML and rule-based approaches
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Database connection
        self.engine = create_engine(config.database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize models
        self._initialize_models()
        
        # Spam patterns and rules
        self.spam_keywords = [
            'congratulations', 'winner', 'free', 'urgent', 'limited time',
            'act now', 'click here', 'call now', 'guaranteed', 'risk-free',
            'no obligation', 'cash', 'money', 'earn', 'income', 'investment',
            'loan', 'credit', 'debt', 'refinance', 'mortgage', 'insurance',
            'pharmacy', 'medication', 'pills', 'viagra', 'cialis'
        ]
        
        self.urgency_patterns = [
            r'act\s+now', r'limited\s+time', r'expires\s+today',
            r'urgent\s+response', r'immediate\s+action', r'don\'t\s+wait'
        ]
        
        self.phone_patterns = [
            r'\b1-?800-?\d{3}-?\d{4}\b',  # 1-800 numbers
            r'\b\d{3}-?\d{3}-?\d{4}\b',   # Standard phone format
            r'\(\d{3}\)\s?\d{3}-?\d{4}'   # (xxx) xxx-xxxx format
        ]
        
    def _initialize_models(self):
        """Initialize ML models for spam detection"""
        try:
            # BERT-based spam classifier
            self.spam_classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # TF-IDF vectorizer for text features
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Random Forest for behavioral analysis
            self.behavior_classifier = RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )
            
            # Isolation Forest for anomaly detection
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Feature scaler
            self.scaler = StandardScaler()
            
            # Load pre-trained models if available
            self._load_pretrained_models()
            
        except Exception as e:
            logger.error(f"Error initializing spam detection models: {e}")
    
    def _load_pretrained_models(self):
        """Load pre-trained models from disk"""
        try:
            # Try to load saved models
            self.behavior_classifier = joblib.load('models/behavior_classifier.pkl')
            self.anomaly_detector = joblib.load('models/anomaly_detector.pkl')
            self.scaler = joblib.load('models/feature_scaler.pkl')
            self.tfidf_vectorizer = joblib.load('models/tfidf_vectorizer.pkl')
            logger.info("Loaded pre-trained spam detection models")
        except FileNotFoundError:
            logger.info("No pre-trained models found, using default initialization")
        except Exception as e:
            logger.error(f"Error loading pre-trained models: {e}")
    
    def analyze_text_spam(self, text: str, phone_number: str = None) -> Dict[str, Any]:
        """Comprehensive text spam analysis"""
        try:
            spam_score = 0.0
            spam_indicators = []
            
            # 1. BERT-based classification
            bert_result = self.spam_classifier(text)[0]
            bert_spam_score = bert_result['score'] if bert_result['label'] == 'TOXIC' else 1 - bert_result['score']
            spam_score += bert_spam_score * 0.4
            
            # 2. Keyword-based detection
            text_lower = text.lower()
            keyword_matches = [kw for kw in self.spam_keywords if kw in text_lower]
            keyword_score = min(len(keyword_matches) / 5, 1.0)  # Normalize to 0-1
            spam_score += keyword_score * 0.2
            
            if keyword_matches:
                spam_indicators.append(f"Spam keywords: {', '.join(keyword_matches)}")
            
            # 3. Urgency pattern detection
            urgency_matches = []
            for pattern in self.urgency_patterns:
                if re.search(pattern, text_lower):
                    urgency_matches.append(pattern)
            
            urgency_score = min(len(urgency_matches) / 3, 1.0)
            spam_score += urgency_score * 0.15
            
            if urgency_matches:
                spam_indicators.append("Contains urgency patterns")
            
            # 4. Phone number analysis
            phone_score = 0.0
            if phone_number:
                phone_analysis = self._analyze_phone_number(phone_number)
                phone_score = phone_analysis['spam_score']
                spam_score += phone_score * 0.15
                
                if phone_analysis['is_suspicious']:
                    spam_indicators.extend(phone_analysis['indicators'])
            
            # 5. Text structure analysis
            structure_score = self._analyze_text_structure(text)
            spam_score += structure_score * 0.1
            
            # Final spam classification
            is_spam = spam_score > 0.6
            confidence = min(spam_score, 1.0)
            
            # Store pattern if it's spam
            if is_spam:
                self._store_spam_pattern(text, 'text', confidence)
            
            return {
                'is_spam': is_spam,
                'spam_score': confidence,
                'confidence': confidence,
                'indicators': spam_indicators,
                'analysis_details': {
                    'bert_score': bert_spam_score,
                    'keyword_score': keyword_score,
                    'urgency_score': urgency_score,
                    'phone_score': phone_score,
                    'structure_score': structure_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text spam: {e}")
            return {
                'is_spam': False,
                'spam_score': 0.0,
                'confidence': 0.0,
                'indicators': [],
                'error': str(e)
            }
    
    def analyze_call_spam(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze call for spam characteristics"""
        try:
            spam_score = 0.0
            spam_indicators = []
            
            phone_number = call_data.get('from_number', '')
            duration = call_data.get('duration_seconds', 0)
            time_of_day = call_data.get('time_of_day', datetime.now().hour)
            transcript = call_data.get('transcript', '')
            
            # 1. Phone number analysis
            phone_analysis = self._analyze_phone_number(phone_number)
            spam_score += phone_analysis['spam_score'] * 0.3
            if phone_analysis['is_suspicious']:
                spam_indicators.extend(phone_analysis['indicators'])
            
            # 2. Call duration analysis
            duration_score = self._analyze_call_duration(duration)
            spam_score += duration_score * 0.2
            if duration_score > 0.5:
                spam_indicators.append("Suspicious call duration")
            
            # 3. Time pattern analysis
            time_score = self._analyze_call_timing(time_of_day)
            spam_score += time_score * 0.15
            if time_score > 0.5:
                spam_indicators.append("Called at suspicious time")
            
            # 4. Transcript analysis (if available)
            if transcript:
                transcript_analysis = self.analyze_text_spam(transcript, phone_number)
                spam_score += transcript_analysis['spam_score'] * 0.35
                if transcript_analysis['is_spam']:
                    spam_indicators.append("Spam content detected in transcript")
            
            # 5. Behavioral pattern analysis
            behavior_features = self._extract_call_behavior_features(call_data)
            behavior_score = self._analyze_call_behavior(behavior_features)
            spam_score += behavior_score * 0.1
            
            # Final classification
            is_spam = spam_score > 0.6
            confidence = min(spam_score, 1.0)
            
            # Store pattern if it's spam
            if is_spam:
                self._store_spam_pattern(
                    f"Call from {phone_number}: {transcript[:100]}...",
                    'call',
                    confidence
                )
            
            return {
                'is_spam': is_spam,
                'spam_score': confidence,
                'confidence': confidence,
                'indicators': spam_indicators,
                'analysis_details': {
                    'phone_score': phone_analysis['spam_score'],
                    'duration_score': duration_score,
                    'time_score': time_score,
                    'transcript_score': transcript_analysis.get('spam_score', 0) if transcript else 0,
                    'behavior_score': behavior_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing call spam: {e}")
            return {
                'is_spam': False,
                'spam_score': 0.0,
                'confidence': 0.0,
                'indicators': [],
                'error': str(e)
            }
    
    def _analyze_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Analyze phone number for spam characteristics"""
        try:
            spam_score = 0.0
            indicators = []
            
            # Parse phone number
            try:
                parsed = phonenumbers.parse(phone_number, "US")
                is_valid = phonenumbers.is_valid_number(parsed)
                
                if not is_valid:
                    spam_score += 0.3
                    indicators.append("Invalid phone number format")
                
                # Check for toll-free numbers (often used by spammers)
                if phone_number.startswith(('800', '888', '877', '866', '855', '844', '833')):
                    spam_score += 0.2
                    indicators.append("Toll-free number")
                
                # Check for sequential or repeated digits
                digits_only = re.sub(r'\D', '', phone_number)
                if self._has_suspicious_digit_pattern(digits_only):
                    spam_score += 0.4
                    indicators.append("Suspicious digit pattern")
                
            except phonenumbers.NumberParseException:
                spam_score += 0.5
                indicators.append("Unparseable phone number")
            
            # Check against known spam patterns in database
            known_spam = self.session.query(SpamPattern).filter(
                SpamPattern.pattern_type == 'phone',
                SpamPattern.pattern_value == phone_number
            ).first()
            
            if known_spam:
                spam_score += 0.5
                indicators.append("Known spam phone number")
            
            return {
                'spam_score': spam_score,
                'is_suspicious': spam_score > 0.3,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Error analyzing phone number: {e}")
            return {
                'spam_score': 0.0,
                'is_suspicious': False,
                'indicators': []
            }
    
    def _analyze_call_duration(self, duration: int) -> float:
        """Analyze call duration for spam characteristics"""
        if duration == 0:
            return 0.0
        
        # Very short calls (less than 5 seconds) might be spam
        if duration < 5:
            return 0.6
        
        # Very long calls might be legitimate
        if duration > 300:  # 5 minutes
            return 0.1
        
        # Medium duration calls are generally normal
        return 0.0
    
    def _analyze_call_timing(self, hour: int) -> float:
        """Analyze call timing for spam characteristics"""
        # Calls during late night hours (10 PM - 6 AM) are more suspicious
        if hour >= 22 or hour <= 6:
            return 0.4
        
        # Calls during early morning hours (6 AM - 9 AM) are also suspicious
        if 6 <= hour <= 9:
            return 0.2
        
        return 0.0
    
    def _extract_call_behavior_features(self, call_data: Dict[str, Any]) -> List[float]:
        """Extract behavioral features from call data"""
        features = []
        
        # Add duration feature
        duration = call_data.get('duration_seconds', 0)
        features.append(duration)
        
        # Add time of day feature
        time_of_day = call_data.get('time_of_day', datetime.now().hour)
        features.append(time_of_day)
        
        # Add frequency feature (this would require historical data)
        # For now, we'll just add a placeholder
        features.append(0.0)
        
        return features
    
    def _analyze_call_behavior(self, features: List[float]) -> float:
        """Analyze call behavior using ML model"""
        try:
            # Scale features
            scaled_features = self.scaler.transform([features])
            
            # Use Random Forest for behavior analysis
            prediction = self.behavior_classifier.predict_proba(scaled_features)[0][1]  # Probability of spam
            return prediction
            
        except Exception as e:
            logger.error(f"Error analyzing call behavior: {e}")
            return 0.0
    
    def _analyze_text_structure(self, text: str) -> float:
        """Analyze text structure for spam characteristics"""
        try:
            # Check for excessive capitalization
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
            caps_score = min(caps_ratio * 5, 1.0)
            
            # Check for excessive punctuation
            punct_count = sum(1 for c in text if c in '!@#$%^&*()')
            punct_score = min(punct_count / 10, 1.0)
            
            # Check for excessive exclamation marks
            excl_count = text.count('!')
            excl_score = min(excl_count / 5, 1.0)
            
            # Check for repetitive words
            words = text.lower().split()
            if len(words) > 0:
                unique_ratio = len(set(words)) / len(words)
                repeat_score = 1.0 - unique_ratio
            else:
                repeat_score = 0.0
            
            # Combine scores
            total_score = (caps_score * 0.3 + 
                          punct_score * 0.2 + 
                          excl_score * 0.3 + 
                          repeat_score * 0.2)
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing text structure: {e}")
            return 0.0
    
    def _has_suspicious_digit_pattern(self, digits: str) -> bool:
        """Check if phone number has suspicious digit patterns"""
        # Check for sequential digits
        for i in range(len(digits) - 2):
            if (int(digits[i+1]) == int(digits[i]) + 1 and 
                int(digits[i+2]) == int(digits[i+1]) + 1):
                return True
        
        # Check for repeated digits
        for i in range(len(digits) - 3):
            if (digits[i] == digits[i+1] == digits[i+2] == digits[i+3]):
                return True
        
        return False
    
    def _store_spam_pattern(self, text: str, pattern_type: str, confidence: float):
        """Store detected spam pattern in database"""
        try:
            # Create new spam pattern record
            spam_pattern = SpamPattern(
                pattern_type=pattern_type,
                pattern_value=text[:255],  # Limit length
                confidence=confidence,
                created_at=datetime.utcnow()
            )
            
            self.session.add(spam_pattern)
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error storing spam pattern: {e}")
            self.session.rollback()

    def _has_suspicious_digit_pattern(self, digits: str) -> bool:
        """Check for suspicious digit patterns in phone numbers"""
        if len(digits) < 10:
            return True
        
        # Check for repeated digits (e.g., 1111111111)
        if len(set(digits)) <= 2:
            return True
        
        # Check for sequential patterns (e.g., 1234567890)
        sequential = ''.join([str(i) for i in range(10)])
        if digits in sequential or digits[::-1] in sequential:
            return True
        
        return False
    
    def _analyze_text_structure(self, text: str) -> float:
        """Analyze text structure for spam characteristics"""
        score = 0.0
        
        # Check for excessive capitalization
        if text.isupper() and len(text) > 10:
            score += 0.3
        
        # Check for excessive punctuation
        punct_ratio = len(re.findall(r'[!?]', text)) / max(len(text), 1)
        if punct_ratio > 0.1:
            score += 0.2
        
        # Check for URLs
        if re.search(r'http[s]?://|www\.', text):
            score += 0.3
        
        # Check for excessive numbers
        digit_ratio = len(re.findall(r'\d', text)) / max(len(text), 1)
        if digit_ratio > 0.3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _analyze_call_duration(self, duration: int) -> float:
        """Analyze call duration for spam patterns"""
        # Very short calls (< 10 seconds) are often spam
        if duration < 10:
            return 0.8
        
        # Very long calls (> 30 minutes) might be robocalls
        if duration > 1800:
            return 0.6
        
        # Normal duration range
        if 30 <= duration <= 300:
            return 0.1
        
        return 0.4
    
    def _analyze_call_timing(self, hour: int) -> float:
        """Analyze call timing for spam patterns"""
        # Early morning (5-8 AM) or late evening (9-11 PM) calls are suspicious
        if 5 <= hour <= 8 or 21 <= hour <= 23:
            return 0.6
        
        # Very late night or very early morning calls
        if hour < 5 or hour > 23:
            return 0.9
        
        # Business hours are less suspicious
        if 9 <= hour <= 17:
            return 0.1
        
        return 0.3
    
    def _extract_call_behavior_features(self, call_data: Dict[str, Any]) -> List[float]:
        """Extract behavioral features from call data"""
        features = []
        
        # Call frequency features
        phone_number = call_data.get('from_number', '')
        recent_calls = self._get_recent_call_count(phone_number, days=7)
        features.append(min(recent_calls / 10, 1.0))  # Normalize
        
        # Time-based features
        hour = call_data.get('time_of_day', datetime.now().hour)
        features.append(hour / 24.0)  # Normalize hour
        
        # Duration features
        duration = call_data.get('duration_seconds', 0)
        features.append(min(duration / 3600, 1.0))  # Normalize to hours
        
        # Day of week (weekends might be more suspicious)
        day_of_week = datetime.now().weekday()
        features.append(day_of_week / 7.0)
        
        return features
    
    def _analyze_call_behavior(self, features: List[float]) -> float:
        """Analyze call behavior using ML model"""
        try:
            if len(features) < 4:
                return 0.0
            
            # Use isolation forest for anomaly detection
            features_array = np.array(features).reshape(1, -1)
            anomaly_score = self.anomaly_detector.decision_function(features_array)[0]
            
            # Convert to 0-1 scale (more negative = more anomalous)
            normalized_score = max(0, min(1, (0.5 - anomaly_score) * 2))
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"Error analyzing call behavior: {e}")
            return 0.0
    
    def _get_recent_call_count(self, phone_number: str, days: int = 7) -> int:
        """Get count of recent calls from a phone number"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Query database for recent calls
            query = """
                SELECT COUNT(*) FROM calls 
                WHERE from_number = %s AND started_at >= %s
            """
            
            result = self.session.execute(query, (phone_number, cutoff_date)).fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting recent call count: {e}")
            return 0
    
    def _store_spam_pattern(self, content: str, pattern_type: str, confidence: float):
        """Store detected spam pattern in database"""
        try:
            pattern = SpamPattern(
                pattern_type=pattern_type,
                content=content[:500],  # Truncate long content
                confidence=confidence,
                detected_at=datetime.now()
            )
            
            self.session.add(pattern)
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error storing spam pattern: {e}")
            self.session.rollback()
    
    def train_models(self, training_data: List[Dict[str, Any]]):
        """Train ML models with new data"""
        try:
            # Prepare training data
            texts = []
            labels = []
            behavior_features = []
            behavior_labels = []
            
            for item in training_data:
                if 'text' in item and 'is_spam' in item:
                    texts.append(item['text'])
                    labels.append(1 if item['is_spam'] else 0)
                
                if 'call_features' in item and 'is_spam' in item:
                    behavior_features.append(item['call_features'])
                    behavior_labels.append(1 if item['is_spam'] else 0)
            
            # Train TF-IDF and behavior classifier
            if texts and labels:
                tfidf_features = self.tfidf_vectorizer.fit_transform(texts)
                # Could train a separate text classifier here
            
            if behavior_features and behavior_labels:
                features_array = np.array(behavior_features)
                scaled_features = self.scaler.fit_transform(features_array)
                
                self.behavior_classifier.fit(scaled_features, behavior_labels)
                
                # Train anomaly detector on normal behavior
                normal_features = scaled_features[np.array(behavior_labels) == 0]
                if len(normal_features) > 0:
                    self.anomaly_detector.fit(normal_features)
            
            # Save trained models
            self._save_models()
            
            # Update metrics
            self._update_model_metrics(len(training_data))
            
            logger.info(f"Successfully trained models with {len(training_data)} samples")
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            import os
            os.makedirs('models', exist_ok=True)
            
            joblib.dump(self.behavior_classifier, 'models/behavior_classifier.pkl')
            joblib.dump(self.anomaly_detector, 'models/anomaly_detector.pkl')
            joblib.dump(self.scaler, 'models/feature_scaler.pkl')
            joblib.dump(self.tfidf_vectorizer, 'models/tfidf_vectorizer.pkl')
            
            logger.info("Saved trained models to disk")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _update_model_metrics(self, training_samples: int):
        """Update model performance metrics"""
        try:
            metrics = MLModelMetrics(
                model_name='spam_detector',
                accuracy=0.0,  # Would calculate from validation set
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                training_samples=training_samples,
                last_trained=datetime.now()
            )
            
            self.session.add(metrics)
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating model metrics: {e}")
            self.session.rollback()
    
    def get_spam_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get spam detection statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get spam call statistics
            call_stats = self.session.execute("""
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN spam_score > 60 THEN 1 ELSE 0 END) as spam_calls
                FROM calls 
                WHERE started_at >= %s
            """, (cutoff_date,)).fetchone()
            
            # Get spam text statistics
            text_stats = self.session.execute("""
                SELECT 
                    COUNT(*) as total_texts,
                    SUM(CASE WHEN spam_flag = true THEN 1 ELSE 0 END) as spam_texts
                FROM texts 
                WHERE ts >= %s
            """, (cutoff_date,)).fetchone()
            
            return {
                'period_days': days,
                'calls': {
                    'total': call_stats[0] if call_stats else 0,
                    'spam': call_stats[1] if call_stats else 0,
                    'spam_rate': (call_stats[1] / max(call_stats[0], 1)) if call_stats else 0
                },
                'texts': {
                    'total': text_stats[0] if text_stats else 0,
                    'spam': text_stats[1] if text_stats else 0,
                    'spam_rate': (text_stats[1] / max(text_stats[0], 1)) if text_stats else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting spam statistics: {e}")
            return {'error': str(e)}
    
    def __del__(self):
        """Cleanup database connection"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
        except:
            pass

    def _analyze_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Analyze phone number for spam characteristics"""
        try:
            spam_score = 0.0
            indicators = []
            
            # Parse phone number
            try:
                parsed = phonenumbers.parse(phone_number, "US")
                is_valid = phonenumbers.is_valid_number(parsed)
                
                if not is_valid:
                    spam_score += 0.3
                    indicators.append("Invalid phone number format")
                
                # Check for toll-free numbers (often used by spammers)
                if phone_number.startswith(('800', '888', '877', '866', '855', '844', '833')):
                    spam_score += 0.2
                    indicators.append("Toll-free number")
                
                # Check for sequential or repeated digits
                digits_only = re.sub(r'\D', '', phone_number)
                if self._has_suspicious_digit_pattern(digits_only):
                    spam_score += 0.4
                    indicators.append("Suspicious digit pattern")
                
            except phonenumbers.NumberParseException:
                spam_score += 0.5
                indicators.append("Unparseable phone number")
            
            # Check against known spam patterns in database
            known_spam = self.session.query(SpamPattern).filter(
                SpamPattern.pattern_type == 'phone',
                SpamPattern.pattern_data.contains(phone_number),
                SpamPattern.is_active == True
            ).first()
            
            if known_spam:
                spam_score += known_spam.confidence_score * 0.8
                indicators.append("Known spam number")
            
            return {
                'spam_score': min(spam_score, 1.0),
                'is_suspicious': spam_score > 0.5,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Error analyzing phone number: {e}")
            return {
                'spam_score': 0.0,
                'is_suspicious': False,
                'indicators': []
            }