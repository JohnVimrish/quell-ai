import torch
import numpy as np
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForCausalLM,
    pipeline, BertTokenizer, BertModel
)
from sentence_transformers import SentenceTransformer
import psycopg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging
from ..models.vector_store import DocumentEmbedding, ConversationContext, SpamPattern
from ..utils.config import Config

logger = logging.getLogger(__name__)

class RAGSystem:
    """
    Advanced RAG system with PostgreSQL vector storage and ML-powered analysis
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize database connection
        self.engine = create_engine(config.database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize transformer models
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.generation_model = AutoModelForCausalLM.from_pretrained(
            "microsoft/DialoGPT-medium"
        ).to(self.device)
        self.generation_tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/DialoGPT-medium"
        )
        
        # NLP pipeline for analysis
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=0 if torch.cuda.is_available() else -1
        )
        
        self.ner_pipeline = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Intent classification
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if torch.cuda.is_available() else -1
        )
        
        self.intent_labels = [
            "urgent_request", "appointment_scheduling", "complaint", "inquiry",
            "sales_pitch", "spam", "emergency", "routine_business", "personal"
        ]
        
    def store_document_embedding(self, user_id: int, content: str, 
                                document_type: str, document_id: int = None,
                                metadata: Dict = None) -> int:
        """Store document embedding in PostgreSQL"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content)
            
            # Create database record
            doc_embedding = DocumentEmbedding(
                user_id=user_id,
                document_type=document_type,
                document_id=document_id,
                content=content,
                embedding=embedding.tolist(),
                metadata=metadata or {}
            )
            
            self.session.add(doc_embedding)
            self.session.commit()
            
            logger.info(f"Stored embedding for document type: {document_type}")
            return doc_embedding.id
            
        except Exception as e:
            logger.error(f"Error storing document embedding: {e}")
            self.session.rollback()
            return None
    
    def retrieve_similar_documents(self, query: str, user_id: int, 
                                 document_types: List[str] = None,
                                 limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar documents using vector similarity search"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Build SQL query for vector similarity
            type_filter = ""
            if document_types:
                type_list = "', '".join(document_types)
                type_filter = f"AND document_type IN ('{type_list}')"
            
            sql_query = text(f"""
                SELECT id, document_type, document_id, content, metadata,
                       1 - (embedding <=> :query_embedding) as similarity_score
                FROM document_embeddings 
                WHERE user_id = :user_id {type_filter}
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
            """)
            
            result = self.session.execute(sql_query, {
                'query_embedding': query_embedding.tolist(),
                'user_id': user_id,
                'limit': limit
            })
            
            documents = []
            for row in result:
                documents.append({
                    'id': row.id,
                    'document_type': row.document_type,
                    'document_id': row.document_id,
                    'content': row.content,
                    'metadata': row.metadata,
                    'similarity_score': float(row.similarity_score)
                })
                
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving similar documents: {e}")
            return []
    
    def analyze_conversation_context(self, conversation_text: str, 
                                   conversation_id: str, user_id: int,
                                   conversation_type: str) -> Dict[str, Any]:
        """Analyze conversation using NLP and store context"""
        try:
            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer(conversation_text)[0]
            sentiment_score = sentiment_result['score'] if sentiment_result['label'] == 'POSITIVE' else -sentiment_result['score']
            
            # Named Entity Recognition
            entities = self.ner_pipeline(conversation_text)
            
            # Intent classification
            intent_result = self.intent_classifier(conversation_text, self.intent_labels)
            primary_intent = intent_result['labels'][0]
            intent_confidence = intent_result['scores'][0]
            
            # Urgency detection (custom logic)
            urgency_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'critical', 'help']
            urgency_score = sum(1 for keyword in urgency_keywords if keyword.lower() in conversation_text.lower()) / len(urgency_keywords)
            
            # Generate context embedding
            context_embedding = self.embedding_model.encode(conversation_text)
            
            # Prepare context data
            context_data = {
                'primary_intent': primary_intent,
                'intent_confidence': float(intent_confidence),
                'sentiment_label': sentiment_result['label'],
                'entities': entities,
                'urgency_keywords_found': [kw for kw in urgency_keywords if kw.lower() in conversation_text.lower()],
                'text_length': len(conversation_text),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Store in database
            conversation_context = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_type=conversation_type,
                context_data=context_data,
                embedding=context_embedding.tolist(),
                entities_extracted=entities,
                sentiment_score=sentiment_score,
                urgency_score=urgency_score,
                                confidence_score=float(intent_confidence)
            )
            
            self.session.add(conversation_context)
            self.session.commit()
            
            return {
                'context_id': conversation_context.id,
                'primary_intent': primary_intent,
                'intent_confidence': float(intent_confidence),
                'sentiment_score': sentiment_score,
                'urgency_score': urgency_score,
                'entities': entities,
                'analysis_complete': True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation context: {e}")
            self.session.rollback()
            return {'analysis_complete': False, 'error': str(e)}
    
    def generate_contextual_response(self, query: str, user_id: int, 
                                   conversation_id: str = None) -> str:
        """Generate AI response using retrieved context and conversation history"""
        try:
            # Retrieve relevant documents
            relevant_docs = self.retrieve_similar_documents(
                query, user_id, 
                document_types=['instruction', 'call_transcript', 'contact_info'],
                limit=3
            )
            
            # Get conversation context if available
            conversation_context = None
            if conversation_id:
                conversation_context = self.session.query(ConversationContext).filter_by(
                    conversation_id=conversation_id,
                    user_id=user_id
                ).order_by(ConversationContext.last_updated.desc()).first()
            
            # Build context for generation
            context_parts = []
            
            # Add relevant documents
            for doc in relevant_docs:
                context_parts.append(f"Reference: {doc['content'][:200]}...")
            
            # Add conversation context
            if conversation_context:
                context_data = conversation_context.context_data
                context_parts.append(f"Intent: {context_data.get('primary_intent', 'unknown')}")
                context_parts.append(f"Sentiment: {context_data.get('sentiment_label', 'neutral')}")
                if context_data.get('urgency_keywords_found'):
                    context_parts.append(f"Urgency indicators: {', '.join(context_data['urgency_keywords_found'])}")
            
            # Create prompt
            context_text = "\n".join(context_parts)
            prompt = f"""Context: {context_text}
User Query: {query}

AI Assistant Response:"""
            
            # Generate response
            inputs = self.generation_tokenizer.encode(prompt, return_tensors='pt').to(self.device)
            
            with torch.no_grad():
                outputs = self.generation_model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 100,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.generation_tokenizer.eos_token_id
                )
            
            response = self.generation_tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    def update_document_usage(self, document_id: int):
        """Update usage statistics for a document"""
        try:
            doc = self.session.query(DocumentEmbedding).filter_by(id=document_id).first()
            if doc:
                doc.usage_count += 1
                doc.last_used = datetime.utcnow()
                self.session.commit()
        except Exception as e:
            logger.error(f"Error updating document usage: {e}")
            self.session.rollback()