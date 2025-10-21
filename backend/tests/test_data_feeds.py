"""
Test suite for data feeds functionality
"""
import pytest
from pathlib import Path

def test_ollama_service_import():
    """Test that OLLama service can be imported"""
    from api.models.ollama_service import OllamaService
    assert OllamaService is not None


def test_file_processors_import():
    """Test that file processors can be imported"""
    from api.utils.file_processors import (
        process_txt,
        process_csv,
        process_xlsx,
        process_text_input,
        validate_file_size
    )
    assert process_txt is not None
    assert process_csv is not None
    assert process_xlsx is not None
    assert process_text_input is not None
    assert validate_file_size is not None


def test_metadata_extractor_import():
    """Test that metadata extractor can be imported"""
    from api.utils.metadata_extractor import (
        extract_key_concepts,
        build_vector_metadata,
        extract_emails,
        extract_phone_numbers
    )
    assert extract_key_concepts is not None
    assert build_vector_metadata is not None
    assert extract_emails is not None
    assert extract_phone_numbers is not None


def test_file_size_validation():
    """Test file size validation"""
    from api.utils.file_processors import validate_file_size
    
    # Valid size
    is_valid, error = validate_file_size(50 * 1024 * 1024)  # 50 MB
    assert is_valid is True
    assert error is None
    
    # Invalid size (over 100MB)
    is_valid, error = validate_file_size(150 * 1024 * 1024)  # 150 MB
    assert is_valid is False
    assert error is not None
    assert "100 MB limit" in error


def test_text_processing():
    """Test text input processing"""
    from api.utils.file_processors import process_text_input
    
    result = process_text_input("Hello, this is a test", "Test Input")
    assert result["success"] is True
    assert result["content"] == "Hello, this is a test"
    assert result["metadata"]["file_type"] == "text_input"
    assert result["metadata"]["word_count"] == 5


def test_email_extraction():
    """Test email extraction from text"""
    from api.utils.metadata_extractor import extract_emails
    
    text = "Contact john.doe@example.com or jane@test.org"
    emails = extract_emails(text)
    assert len(emails) == 2
    assert "john.doe@example.com" in emails
    assert "jane@test.org" in emails


def test_phone_extraction():
    """Test phone number extraction"""
    from api.utils.metadata_extractor import extract_phone_numbers
    
    text = "Call me at 555-123-4567 or (555) 987-6543"
    phones = extract_phone_numbers(text)
    assert len(phones) >= 1  # At least one phone number found


def test_key_concepts_extraction():
    """Test key concepts extraction"""
    from api.utils.metadata_extractor import extract_key_concepts
    
    text = """
    If john.vimri@gmail.com or vimrish.john@gmail.com asks for the 
    classified document, let them know it is under this location.
    """
    
    concepts = extract_key_concepts(text)
    assert "emails" in concepts
    assert len(concepts["emails"]) == 2
    assert "summary" in concepts


def test_vector_metadata_building():
    """Test vector metadata building"""
    from api.utils.metadata_extractor import build_vector_metadata
    
    concepts = {
        "emails": ["test@example.com"],
        "document_references": ["report.pdf"],
        "key_phrases": ["classified document"],
    }
    
    metadata = build_vector_metadata(concepts, document_id=123)
    assert "_meta" in metadata
    assert metadata["_meta"]["document_id"] == 123
    assert len(metadata) > 1  # Should have vector keys


def test_ollama_service_initialization():
    """Test OLLama service initialization"""
    from api.models.ollama_service import OllamaService
    
    # Initialize with non-existent path (should not crash)
    service = OllamaService(model_path="/nonexistent/path")
    assert service is not None
    assert service.is_available() is False  # Model won't load
    
    # Zero vector should still work
    zero_vec = service._zero_vector()
    assert len(zero_vec) == 384
    assert all(v == 0.0 for v in zero_vec)


def test_document_model_fields():
    """Test that document model has new fields"""
    from functionalities.document import Document
    
    # Check that new attributes exist
    assert hasattr(Document, 'file_type')
    assert hasattr(Document, 'file_size_bytes')
    assert hasattr(Document, 'original_content')
    assert hasattr(Document, 'processed_content')
    assert hasattr(Document, 'content_metadata')
    assert hasattr(Document, 'embedding')
    assert hasattr(Document, 'vector_metadata')
    assert hasattr(Document, 'ollama_model')


def test_csv_processing():
    """Test CSV file processing"""
    from api.utils.file_processors import process_csv
    
    # Create sample CSV data
    csv_data = b"Name,Age,City\nJohn,30,NYC\nJane,25,LA"
    
    result = process_csv(csv_data, "test.csv")
    assert result["success"] is True
    assert result["metadata"]["row_count"] == 2
    assert result["metadata"]["column_count"] == 3
    assert "Name" in result["metadata"]["columns"]


def test_txt_processing():
    """Test TXT file processing"""
    from api.utils.file_processors import process_txt
    
    txt_data = b"This is a test file.\nIt has multiple lines.\nThird line here."
    
    result = process_txt(txt_data, "test.txt")
    assert result["success"] is True
    assert result["metadata"]["line_count"] == 3
    assert "This is a test file" in result["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

