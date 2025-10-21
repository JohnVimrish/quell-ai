"""
Metadata extraction utilities for building semantic search mappings.
Extracts key concepts, entities, and creates vector metadata for efficient retrieval.
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from api.models.ollama_service import OllamaService

logger = logging.getLogger(__name__)


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text."""
    # Match various phone number formats
    phone_pattern = r'\+?1?\s*\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}'
    return re.findall(phone_pattern, text)


def extract_document_references(text: str) -> List[str]:
    """Extract document names and references from text."""
    # Look for common document patterns
    doc_patterns = [
        r'\b([A-Z][a-z]+\s+[A-Z][a-z]+\.(?:pdf|docx|xlsx|txt))\b',  # TitleCase.ext
        r'\b(document[s]?\s+named?\s+["\']([^"\']+)["\'])',  # document named "..."
        r'\b(file[s]?\s+named?\s+["\']([^"\']+)["\'])',  # file named "..."
        r'\b([a-zA-Z0-9_-]+\.(?:pdf|docx|xlsx|txt|csv))\b',  # filename.ext
    ]
    
    references = []
    for pattern in doc_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                references.extend([m for m in match if m])
            else:
                references.append(match)
    
    return list(set(references))  # Remove duplicates


def extract_names(text: str) -> List[str]:
    """Extract potential names from text (simplified pattern matching)."""
    # Look for capitalized words that might be names
    name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    potential_names = re.findall(name_pattern, text)
    
    # Filter out common non-name phrases
    stopwords = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'Who', 'Why', 'How'}
    names = [name for name in potential_names if not any(word in stopwords for word in name.split())]
    
    return names[:10]  # Limit to top 10 to avoid noise


def extract_key_phrases(text: str, max_phrases: int = 20) -> List[str]:
    """
    Extract key phrases from text using simple NLP techniques.
    
    Args:
        text: Input text
        max_phrases: Maximum number of phrases to extract
        
    Returns:
        List of key phrases
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    
    key_phrases = []
    
    # Look for quoted text (often important)
    quoted = re.findall(r'["\']([^"\']+)["\']', text)
    key_phrases.extend(quoted[:5])
    
    # Look for noun phrases (simplified: sequences of capitalized words)
    for sentence in sentences[:20]:  # Limit to first 20 sentences
        caps_phrases = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b', sentence)
        key_phrases.extend(caps_phrases)
    
    # Look for phrases after keywords
    important_keywords = ['classified', 'confidential', 'important', 'location', 'document', 'file']
    for keyword in important_keywords:
        pattern = rf'\b{keyword}\b\s+(\w+(?:\s+\w+){{0,4}})'
        matches = re.findall(pattern, text, re.IGNORECASE)
        key_phrases.extend(matches)
    
    # Remove duplicates and limit
    unique_phrases = []
    seen = set()
    for phrase in key_phrases:
        phrase_lower = phrase.lower().strip()
        if phrase_lower and phrase_lower not in seen and len(phrase_lower) > 3:
            unique_phrases.append(phrase)
            seen.add(phrase_lower)
        if len(unique_phrases) >= max_phrases:
            break
    
    return unique_phrases


def extract_key_concepts(
    content: str,
    ollama_service: Optional[OllamaService] = None
) -> Dict[str, Any]:
    """
    Extract key concepts, entities, and keywords from content.
    
    Args:
        content: Text content to analyze
        ollama_service: Optional OLLama service for advanced extraction
        
    Returns:
        Dictionary containing extracted concepts and entities
    """
    if not content or not content.strip():
        return {
            "emails": [],
            "phone_numbers": [],
            "document_references": [],
            "names": [],
            "key_phrases": [],
            "summary": "",
        }
    
    try:
        # Extract entities
        emails = extract_emails(content)
        phone_numbers = extract_phone_numbers(content)
        document_refs = extract_document_references(content)
        names = extract_names(content)
        key_phrases = extract_key_phrases(content)
        
        # Create summary (first 200 chars)
        summary = content[:200].strip()
        if len(content) > 200:
            summary += "..."
        
        return {
            "emails": emails,
            "phone_numbers": phone_numbers,
            "document_references": document_refs,
            "names": names,
            "key_phrases": key_phrases,
            "summary": summary,
            "entity_count": len(emails) + len(phone_numbers) + len(names),
        }
        
    except Exception as exc:
        logger.error(f"Error extracting key concepts: {exc}", exc_info=True)
        return {
            "emails": [],
            "phone_numbers": [],
            "document_references": [],
            "names": [],
            "key_phrases": [],
            "summary": "",
            "error": str(exc),
        }


def build_vector_metadata(
    concepts: Dict[str, Any],
    embeddings: Optional[List[float]] = None,
    document_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build vector metadata mapping for semantic retrieval.
    
    Creates a JSON structure mapping vector keys to table/document locations.
    Format: {"vector_key_123": ["table_1", "document_5"], ...}
    
    Args:
        concepts: Extracted concepts dictionary
        embeddings: Optional embedding vector
        document_id: Optional document ID for reference
        
    Returns:
        Vector metadata dictionary
    """
    metadata = {}
    
    try:
        # Create a hash-based key for this content
        base_key = f"doc_{document_id}" if document_id else "content"
        
        # Map important entities to document location
        important_items = []
        
        # Add emails
        for email in concepts.get("emails", []):
            important_items.append(("email", email))
        
        # Add document references
        for doc_ref in concepts.get("document_references", []):
            important_items.append(("document", doc_ref))
        
        # Add key phrases
        for phrase in concepts.get("key_phrases", [])[:10]:  # Top 10 phrases
            important_items.append(("phrase", phrase))
        
        # Create vector keys for each important item
        for item_type, item_value in important_items:
            # Create a unique key based on the item
            item_hash = hashlib.md5(item_value.lower().encode()).hexdigest()[:10]
            vector_key = f"vector_{item_type}_{item_hash}"
            
            # Map to document/table location
            if vector_key not in metadata:
                metadata[vector_key] = []
            
            location = f"{base_key}_{item_type}"
            if location not in metadata[vector_key]:
                metadata[vector_key].append(location)
        
        # Add a general embedding key if embeddings provided
        if embeddings:
            # Create a key based on embedding signature
            embedding_sig = hashlib.md5(
                str(embeddings[:10]).encode()
            ).hexdigest()[:10]
            vector_key = f"vector_embed_{embedding_sig}"
            metadata[vector_key] = [base_key]
        
        # Add metadata about the mapping
        metadata["_meta"] = {
            "total_keys": len(metadata) - 1,  # Exclude _meta itself
            "document_id": document_id,
            "entity_count": concepts.get("entity_count", 0),
        }
        
        return metadata
        
    except Exception as exc:
        logger.error(f"Error building vector metadata: {exc}", exc_info=True)
        return {"_meta": {"error": str(exc)}}


def extract_table_references(content: str) -> List[str]:
    """
    Extract potential database table references from content.
    
    Args:
        content: Text content to analyze
        
    Returns:
        List of potential table names
    """
    # Look for patterns like "table_name", "TableName", etc.
    table_patterns = [
        r'\b([a-z_]+_table)\b',  # snake_case_table
        r'\btable\s+([a-z_]+)\b',  # table name_here
        r'\b([A-Z][a-zA-Z]+Table)\b',  # CamelCaseTable
    ]
    
    tables = []
    for pattern in table_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        tables.extend(matches)
    
    return list(set(tables))


def create_search_index_data(
    content: str,
    concepts: Dict[str, Any],
    embeddings: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Create complete search index data for a document.
    
    Args:
        content: Document content
        concepts: Extracted concepts
        embeddings: Embedding vector
        
    Returns:
        Complete index data structure
    """
    return {
        "searchable_text": content,
        "entities": {
            "emails": concepts.get("emails", []),
            "phones": concepts.get("phone_numbers", []),
            "names": concepts.get("names", []),
            "documents": concepts.get("document_references", []),
        },
        "key_phrases": concepts.get("key_phrases", []),
        "summary": concepts.get("summary", ""),
        "embedding_available": embeddings is not None,
        "table_references": extract_table_references(content),
    }

