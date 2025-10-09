import os
import logging
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import librosa
import soundfile as sf
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import json

logger = logging.getLogger(__name__)

class VoiceModel:
    """
    Voice model for training and generating synthetic voice samples.
    Handles voice cloning with transparency and quality assessment.
    """
    
    def __init__(self, model_path: str = "models/voice/", sample_rate: int = 22050):
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self.model_data = {}
        self.is_trained = False
        self.quality_threshold = 0.75
        self.min_samples_required = 10
        
        # Ensure model directory exists
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Voice feature extraction parameters
        self.feature_config = {
            'n_mfcc': 13,
            'n_fft': 2048,
            'hop_length': 512,
            'n_mels': 128,
            'fmin': 0,
            'fmax': None
        }
        
        logger.info(f"VoiceModel initialized with path: {self.model_path}")
    
    def extract_voice_features(self, audio_path: str) -> Dict:
        """
        Extract voice features from audio file for training and comparison.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing extracted features
        """
        try:
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Extract various voice features
            features = {}
            
            # MFCC features (spectral characteristics)
            mfcc = librosa.feature.mfcc(
                y=audio, 
                sr=sr, 
                n_mfcc=self.feature_config['n_mfcc'],
                n_fft=self.feature_config['n_fft'],
                hop_length=self.feature_config['hop_length']
            )
            features['mfcc'] = np.mean(mfcc.T, axis=0)
            features['mfcc_std'] = np.std(mfcc.T, axis=0)
            
            # Mel-frequency cepstral coefficients
            mel_spectrogram = librosa.feature.melspectrogram(
                y=audio,
                sr=sr,
                n_mels=self.feature_config['n_mels'],
                n_fft=self.feature_config['n_fft'],
                hop_length=self.feature_config['hop_length']
            )
            features['mel_mean'] = np.mean(mel_spectrogram, axis=1)
            features['mel_std'] = np.std(mel_spectrogram, axis=1)
            
            # Pitch and fundamental frequency
            pitches, magnitudes = librosa.piptrack(
                y=audio, 
                sr=sr, 
                threshold=0.1
            )
            pitch_values = pitches[magnitudes > np.median(magnitudes)]
            if len(pitch_values) > 0:
                features['pitch_mean'] = np.mean(pitch_values)
                features['pitch_std'] = np.std(pitch_values)
            else:
                features['pitch_mean'] = 0
                features['pitch_std'] = 0
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            features['spectral_centroid_mean'] = np.mean(spectral_centroids)
            features['spectral_centroid_std'] = np.std(spectral_centroids)
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            features['spectral_rolloff_mean'] = np.mean(spectral_rolloff)
            features['spectral_rolloff_std'] = np.std(spectral_rolloff)
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            features['zcr_mean'] = np.mean(zcr)
            features['zcr_std'] = np.std(zcr)
            
            # Audio duration and energy
            features['duration'] = len(audio) / sr
            features['energy'] = np.sum(audio ** 2)
            features['rms_energy'] = np.sqrt(np.mean(audio ** 2))
            
            logger.debug(f"Extracted features from {audio_path}")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features from {audio_path}: {e}")
            raise
    
    def assess_sample_quality(self, audio_path: str, reference_features: Optional[Dict] = None) -> float:
        """
        Assess the quality of a voice sample.
        
        Args:
            audio_path: Path to audio file
            reference_features: Reference features for comparison
            
        Returns:
            Quality score between 0 and 1
        """
        try:
            features = self.extract_voice_features(audio_path)
            
            # Basic quality checks
            quality_score = 1.0
            
            # Check duration (should be between 3-30 seconds)
            duration = features['duration']
            if duration < 3:
                quality_score *= 0.5  # Too short
            elif duration > 30:
                quality_score *= 0.7  # Too long
            
            # Check energy levels (avoid too quiet or too loud)
            rms_energy = features['rms_energy']
            if rms_energy < 0.01:
                quality_score *= 0.6  # Too quiet
            elif rms_energy > 0.5:
                quality_score *= 0.8  # Too loud
            
            # Check for silence (high zero crossing rate might indicate noise)
            if features['zcr_mean'] > 0.3:
                quality_score *= 0.7  # Potentially noisy
            
            # If we have reference features, compare similarity
            if reference_features and self.model_data.get('reference_features'):
                similarity = self.calculate_voice_similarity(features, reference_features)
                quality_score *= similarity
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error assessing sample quality: {e}")
            return 0.0
    
    def calculate_voice_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Calculate similarity between two voice feature sets.
        
        Args:
            features1: First feature set
            features2: Second feature set
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Compare key features
            similarities = []
            
            # MFCC similarity
            if 'mfcc' in features1 and 'mfcc' in features2:
                mfcc_sim = cosine_similarity(
                    features1['mfcc'].reshape(1, -1),
                    features2['mfcc'].reshape(1, -1)
                )[0][0]
                similarities.append(mfcc_sim)
            
            # Pitch similarity
            if all(k in features1 and k in features2 for k in ['pitch_mean', 'pitch_std']):
                pitch_diff = abs(features1['pitch_mean'] - features2['pitch_mean'])
                pitch_sim = max(0, 1 - (pitch_diff / 500))  # Normalize by typical pitch range
                similarities.append(pitch_sim)
            
            # Spectral similarity
            if all(k in features1 and k in features2 for k in ['spectral_centroid_mean']):
                spectral_diff = abs(features1['spectral_centroid_mean'] - features2['spectral_centroid_mean'])
                spectral_sim = max(0, 1 - (spectral_diff / 5000))  # Normalize
                similarities.append(spectral_sim)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating voice similarity: {e}")
            return 0.0
    
    def add_training_sample(self, audio_path: str, text: str, user_id: int) -> Dict:
        """
        Add a training sample to the voice model.
        
        Args:
            audio_path: Path to audio file
            text: Text that was spoken
            user_id: User ID for the voice model
            
        Returns:
            Dictionary with sample information and quality assessment
        """
        try:
            # Extract features
            features = self.extract_voice_features(audio_path)
            
            # Assess quality
            reference_features = self.model_data.get('reference_features')
            quality_score = self.assess_sample_quality(audio_path, reference_features)
            
            # Create sample record
            sample_data = {
                'audio_path': audio_path,
                'text': text,
                'features': features,
                'quality_score': quality_score,
                'duration': features['duration'],
                'added_at': datetime.utcnow().isoformat(),
                'user_id': user_id
            }
            
            # Initialize model data if needed
            if 'samples' not in self.model_data:
                self.model_data['samples'] = []
                self.model_data['user_id'] = user_id
                self.model_data['reference_features'] = features  # First sample as reference
            
            # Add sample
            self.model_data['samples'].append(sample_data)
            
            # Update model statistics
            self._update_model_stats()
            
            logger.info(f"Added training sample with quality score: {quality_score:.2f}")
            
            return {
                'sample_id': len(self.model_data['samples']) - 1,
                'quality_score': quality_score,
                'total_samples': len(self.model_data['samples']),
                'ready_for_training': self.is_ready_for_training()
            }
            
        except Exception as e:
            logger.error(f"Error adding training sample: {e}")
            raise
    
    def _update_model_stats(self):
        """Update model statistics based on current samples."""
        if not self.model_data.get('samples'):
            return
        
        samples = self.model_data['samples']
        
        # Calculate average quality
        quality_scores = [s['quality_score'] for s in samples]
        self.model_data['average_quality'] = np.mean(quality_scores)
        
        # Calculate total duration
        total_duration = sum(s['duration'] for s in samples)
        self.model_data['total_duration'] = total_duration
        
        # Update sample count
        self.model_data['sample_count'] = len(samples)
        
        # Update last modified
        self.model_data['last_updated'] = datetime.utcnow().isoformat()
    
    def is_ready_for_training(self) -> bool:
        """
        Check if the model has enough samples for training.
        
        Returns:
            True if ready for training
        """
        if not self.model_data.get('samples'):
            return False
        
        sample_count = len(self.model_data['samples'])
        avg_quality = self.model_data.get('average_quality', 0)
        total_duration = self.model_data.get('total_duration', 0)
        
        return (
            sample_count >= self.min_samples_required and            avg_quality >= self.quality_threshold and
            total_duration >= 60  # At least 1 minute of audio
        )
    
    def train_model(self, model_name: str) -> Dict:
        """
        Train the voice model using collected samples.
        
        Args:
            model_name: Name for the trained model
            
        Returns:
            Training results and model information
        """
        try:
            if not self.is_ready_for_training():
                raise ValueError("Not enough quality samples for training")
            
            logger.info(f"Starting voice model training: {model_name}")
            
            # Prepare training data
            training_features = []
            training_texts = []
            
            for sample in self.model_data['samples']:
                if sample['quality_score'] >= self.quality_threshold:
                    training_features.append(sample['features'])
                    training_texts.append(sample['text'])
            
            # Create voice profile (simplified approach)
            voice_profile = self._create_voice_profile(training_features)
            
            # Save trained model
            model_file = self.model_path / f"{model_name}.pkl"
            model_info = {
                'model_name': model_name,
                'voice_profile': voice_profile,
                'training_samples': len(training_features),
                'average_quality': self.model_data['average_quality'],
                'trained_at': datetime.utcnow().isoformat(),
                'model_version': '1.0',
                'user_id': self.model_data['user_id']
            }
            
            with open(model_file, 'wb') as f:
                pickle.dump(model_info, f)
            
            # Save metadata
            metadata_file = self.model_path / f"{model_name}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    'model_name': model_name,
                    'training_samples': len(training_features),
                    'quality_score': self.model_data['average_quality'],
                    'trained_at': model_info['trained_at'],
                    'user_id': self.model_data['user_id']
                }, f, indent=2)
            
            self.is_trained = True
            logger.info(f"Voice model training completed: {model_name}")
            
            return {
                'success': True,
                'model_name': model_name,
                'model_path': str(model_file),
                'training_samples': len(training_features),
                'quality_score': self.model_data['average_quality'],
                'model_size_mb': model_file.stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Error training voice model: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_voice_profile(self, training_features: List[Dict]) -> Dict:
        """
        Create a voice profile from training features.
        
        Args:
            training_features: List of feature dictionaries
            
        Returns:
            Voice profile dictionary
        """
        profile = {}
        
        # Calculate mean and std for each feature
        feature_keys = training_features[0].keys()
        
        for key in feature_keys:
            if isinstance(training_features[0][key], (int, float)):
                values = [f[key] for f in training_features]
                profile[f"{key}_mean"] = np.mean(values)
                profile[f"{key}_std"] = np.std(values)
            elif isinstance(training_features[0][key], np.ndarray):
                arrays = [f[key] for f in training_features]
                profile[f"{key}_mean"] = np.mean(arrays, axis=0)
                profile[f"{key}_std"] = np.std(arrays, axis=0)
        
        return profile
    
    def load_model(self, model_name: str) -> bool:
        """
        Load a trained voice model.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            True if loaded successfully
        """
        try:
            model_file = self.model_path / f"{model_name}.pkl"
            
            if not model_file.exists():
                logger.error(f"Model file not found: {model_file}")
                return False
            
            with open(model_file, 'rb') as f:
                self.model_data = pickle.load(f)
            
            self.is_trained = True
            logger.info(f"Voice model loaded: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading voice model: {e}")
            return False
    
    def generate_voice_sample(self, text: str, output_path: str) -> Dict:
        """
        Generate synthetic voice sample (placeholder for actual TTS integration).
        
        Args:
            text: Text to synthesize
            output_path: Path to save generated audio
            
        Returns:
            Generation results
        """
        try:
            if not self.is_trained:
                raise ValueError("Model must be trained before generating samples")
            
            # This is a placeholder - in production, integrate with:
            # - ElevenLabs API
            # - Coqui TTS
            # - Other voice synthesis services
            
            logger.info(f"Generating voice sample for text: {text[:50]}...")
            
            # For now, return metadata about what would be generated
            return {
                'success': True,
                'text': text,
                'output_path': output_path,
                'duration_estimate': len(text) * 0.1,  # Rough estimate
                'model_used': self.model_data.get('model_name', 'unknown'),
                'generated_at': datetime.utcnow().isoformat(),
                'disclosure_required': True  # Always require disclosure for synthetic voice
            }
            
        except Exception as e:
            logger.error(f"Error generating voice sample: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_voice_match(self, audio_path: str, confidence_threshold: float = 0.8) -> Dict:
        """
        Validate if an audio sample matches the trained voice model.
        
        Args:
            audio_path: Path to audio file to validate
            confidence_threshold: Minimum confidence for match
            
        Returns:
            Validation results
        """
        try:
            if not self.is_trained:
                raise ValueError("Model must be trained before validation")
            
            # Extract features from the sample
            sample_features = self.extract_voice_features(audio_path)
            
            # Compare with voice profile
            reference_features = self.model_data.get('voice_profile', {})
            similarity = self.calculate_voice_similarity(sample_features, reference_features)
            
            is_match = similarity >= confidence_threshold
            
            return {
                'is_match': is_match,
                'similarity_score': similarity,
                'confidence_threshold': confidence_threshold,
                'sample_quality': self.assess_sample_quality(audio_path),
                'validated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating voice match: {e}")
            return {
                'is_match': False,
                'error': str(e)
            }
    
    def get_model_info(self) -> Dict:
        """
        Get information about the current voice model.
        
        Returns:
            Model information dictionary
        """
        return {
            'is_trained': self.is_trained,
            'sample_count': len(self.model_data.get('samples', [])),
            'average_quality': self.model_data.get('average_quality', 0),
            'total_duration': self.model_data.get('total_duration', 0),
            'ready_for_training': self.is_ready_for_training(),
            'last_updated': self.model_data.get('last_updated'),
            'user_id': self.model_data.get('user_id'),
            'model_path': str(self.model_path)
        }
    
    def cleanup(self):
        """Clean up resources and temporary files."""
        try:
            # Clear model data from memory
            self.model_data.clear()
            self.is_trained = False
            
            # Clean up temporary files if any
            temp_files = self.model_path.glob("temp_*")
            for temp_file in temp_files:
                temp_file.unlink()
            
            logger.info("Voice model cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during voice model cleanup: {e}")
    
    def export_model(self, export_path: str) -> Dict:
        """
        Export the trained model for backup or transfer.
        
        Args:
            export_path: Path to export the model
            
        Returns:
            Export results
        """
        try:
            if not self.is_trained:
                raise ValueError("No trained model to export")
            
            export_data = {
                'model_data': self.model_data,
                'feature_config': self.feature_config,
                'quality_threshold': self.quality_threshold,
                'exported_at': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            with open(export_path, 'wb') as f:
                pickle.dump(export_data, f)
            
            return {
                'success': True,
                'export_path': export_path,
                'file_size_mb': os.path.getsize(export_path) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Error exporting model: {e}")
            return {
                'success': False,
                'error': str(e)
            }