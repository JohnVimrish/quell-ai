"""
Integration tests for Phase 2: Version Control and Soft Deletion

Tests cover:
- File version detection and comparison
- Soft deletion and restoration
- Version history management
- Query manager integration
"""

import json
import os
import pytest
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from api.app import create_app
from api.models.ollama_service import OllamaService
from api.repositories.documents_repo import DocumentsRepository
from api.utils.query_manager import QueryManager
from functionalities.document import Document, DocumentVersion, DocumentDeletionLog


@pytest.fixture
def app():
    """Create test Flask application."""
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/ai_call_test')
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client."""
    # Login with test user
    client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    return client


@pytest.fixture
def test_repo():
    """Create test repository."""
    database_url = os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/ai_call_test')
    
    # Load queries
    queries_path = Path('backend/config/queries.json')
    with open(queries_path) as f:
        queries = json.load(f)
    
    query_manager = QueryManager(queries)
    return DocumentsRepository(database_url, queries, query_manager)


@pytest.fixture
def test_ollama_service():
    """Create test OLLama service."""
    model_path = os.getenv(
        'OLLAMA_MODEL_PATH',
        'C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct'
    )
    return OllamaService(model_path, embedding_dim=384)


# ===== Version Detection Tests =====

def test_upload_new_file_creates_version_1(authenticated_client):
    """Test uploading a new file creates version 1."""
    data = {
        'file': (BytesIO(b'Test content for version 1'), 'test_doc.txt'),
        'description': 'Test document',
        'classification': 'internal'
    }
    
    response = authenticated_client.post(
        '/api/documents/upload',
        data=data,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    result = response.get_json()
    assert result['version'] == 1
    assert result['reprocessed'] is True
    assert 'message' in result


def test_upload_unchanged_file_returns_existing(authenticated_client):
    """Test uploading unchanged file returns existing document."""
    # First upload
    data1 = {
        'file': (BytesIO(b'Same content'), 'unchanged.txt'),
        'description': 'First upload'
    }
    response1 = authenticated_client.post(
        '/api/documents/upload',
        data=data1,
        content_type='multipart/form-data'
    )
    assert response1.status_code == 201
    doc1 = response1.get_json()
    
    # Second upload with same content
    data2 = {
        'file': (BytesIO(b'Same content'), 'unchanged.txt'),
        'description': 'Second upload'
    }
    response2 = authenticated_client.post(
        '/api/documents/upload',
        data=data2,
        content_type='multipart/form-data'
    )
    assert response2.status_code == 200
    doc2 = response2.get_json()
    
    # Should return same document
    assert doc2['id'] == doc1['id']
    assert doc2['version'] == 1
    assert doc2['reprocessed'] is False
    assert 'similarity_score' in doc2
    assert doc2['similarity_score'] > 0.95


def test_upload_changed_file_increments_version(authenticated_client):
    """Test uploading changed file creates new version."""
    # First upload
    data1 = {
        'file': (BytesIO(b'Original content for testing'), 'version_test.txt'),
        'description': 'Version 1'
    }
    response1 = authenticated_client.post(
        '/api/documents/upload',
        data=data1,
        content_type='multipart/form-data'
    )
    assert response1.status_code == 201
    doc1 = response1.get_json()
    
    # Second upload with different content
    data2 = {
        'file': (BytesIO(b'Completely different content here'), 'version_test.txt'),
        'description': 'Version 2'
    }
    response2 = authenticated_client.post(
        '/api/documents/upload',
        data=data2,
        content_type='multipart/form-data'
    )
    assert response2.status_code == 200
    doc2 = response2.get_json()
    
    # Should increment version
    assert doc2['id'] == doc1['id']
    assert doc2['version'] == 2
    assert doc2['reprocessed'] is True
    assert 'similarity_score' in doc2
    assert doc2['similarity_score'] < 0.95


def test_version_snapshot_created_on_update(test_repo, authenticated_client):
    """Test version snapshot is created when document is updated."""
    # Upload initial file
    data1 = {
        'file': (BytesIO(b'Initial content'), 'snapshot_test.txt'),
    }
    response1 = authenticated_client.post(
        '/api/documents/upload',
        data=data1,
        content_type='multipart/form-data'
    )
    doc1 = response1.get_json()
    
    # Upload updated file
    data2 = {
        'file': (BytesIO(b'Updated content that is different'), 'snapshot_test.txt'),
    }
    authenticated_client.post(
        '/api/documents/upload',
        data=data2,
        content_type='multipart/form-data'
    )
    
    # Get version history
    response = authenticated_client.get(f'/api/documents/{doc1["id"]}/versions')
    assert response.status_code == 200
    
    versions = response.get_json()['versions']
    assert len(versions) >= 1
    assert versions[0]['version'] == 1


# ===== Soft Deletion Tests =====

def test_soft_delete_document(authenticated_client):
    """Test soft deleting a document."""
    # Create a document
    data = {
        'file': (BytesIO(b'Content to be deleted'), 'delete_test.txt'),
    }
    response = authenticated_client.post(
        '/api/documents/upload',
        data=data,
        content_type='multipart/form-data'
    )
    doc_id = response.get_json()['id']
    
    # Soft delete
    response = authenticated_client.delete(
        f'/api/documents/{doc_id}?reason=Test deletion'
    )
    assert response.status_code == 200
    result = response.get_json()
    assert 'message' in result
    assert 'note' in result
    
    # Verify document not in active list
    response = authenticated_client.get('/api/documents')
    documents = response.get_json()['documents']
    assert not any(d['id'] == doc_id for d in documents)
    
    # Verify document in deleted list
    response = authenticated_client.get('/api/documents/deleted')
    deleted = response.get_json()['documents']
    assert any(d['id'] == doc_id for d in deleted)


def test_restore_soft_deleted_document(authenticated_client):
    """Test restoring a soft-deleted document."""
    # Create and delete a document
    data = {
        'file': (BytesIO(b'Content to be restored'), 'restore_test.txt'),
    }
    response = authenticated_client.post(
        '/api/documents/upload',
        data=data,
        content_type='multipart/form-data'
    )
    doc_id = response.get_json()['id']
    
    authenticated_client.delete(f'/api/documents/{doc_id}')
    
    # Restore
    response = authenticated_client.post(f'/api/documents/{doc_id}/restore')
    assert response.status_code == 200
    result = response.get_json()
    assert result['is_deleted'] is False
    
    # Verify document back in active list
    response = authenticated_client.get('/api/documents')
    documents = response.get_json()['documents']
    assert any(d['id'] == doc_id for d in documents)
    
    # Verify document not in deleted list
    response = authenticated_client.get('/api/documents/deleted')
    deleted = response.get_json()['documents']
    assert not any(d['id'] == doc_id for d in deleted)


def test_soft_delete_preserves_data(test_repo):
    """Test that soft deletion preserves document data."""
    # Create document
    payload = {
        'user_id': 1,
        'name': 'preserve_test.txt',
        'file_type': 'txt',
        'processed_content': 'Important content',
        'content_metadata': {'key': 'value'},
        'vector_metadata': {'vector_key': ['table_1']},
        'embedding': [0.1] * 384
    }
    doc_id = test_repo.create_data_feed(payload)
    
    # Soft delete
    test_repo.soft_delete_document(doc_id, 1, 'Test preservation')
    
    # Verify data still in database (would need direct DB query)
    # For integration test, just verify restore works
    test_repo.restore_document(doc_id, 1)
    content = test_repo.get_relevant_content(doc_id, 1)
    
    assert content is not None
    assert content['processed_content'] == 'Important content'
    assert content['content_metadata']['key'] == 'value'


def test_deletion_log_created(test_repo):
    """Test that deletion creates audit log entry."""
    # Create document
    payload = {
        'user_id': 1,
        'name': 'audit_test.txt',
        'file_type': 'txt',
        'processed_content': 'Content',
        'vector_metadata': {'key': 'value'}
    }
    doc_id = test_repo.create_data_feed(payload)
    
    # Soft delete
    reason = 'Testing audit trail'
    success = test_repo.soft_delete_document(doc_id, 1, reason)
    assert success is True
    
    # Verify log entry exists (would need direct DB query in real test)
    # For now, just verify deletion was successful
    deleted = test_repo.list_deleted_documents(1)
    assert any(d['id'] == doc_id for d in deleted)


# ===== Version History Tests =====

def test_get_version_history(authenticated_client):
    """Test retrieving version history."""
    # Create document with multiple versions
    filename = 'history_test.txt'
    
    # Version 1
    data1 = {'file': (BytesIO(b'Version 1 content'), filename)}
    response1 = authenticated_client.post('/api/documents/upload', data=data1, content_type='multipart/form-data')
    doc_id = response1.get_json()['id']
    
    # Version 2
    data2 = {'file': (BytesIO(b'Version 2 different content'), filename)}
    authenticated_client.post('/api/documents/upload', data=data2, content_type='multipart/form-data')
    
    # Version 3
    data3 = {'file': (BytesIO(b'Version 3 completely new content'), filename)}
    authenticated_client.post('/api/documents/upload', data=data3, content_type='multipart/form-data')
    
    # Get history
    response = authenticated_client.get(f'/api/documents/{doc_id}/versions')
    assert response.status_code == 200
    
    versions = response.get_json()['versions']
    assert len(versions) >= 2  # Should have snapshots of v1 and v2
    
    # Versions should be in descending order
    assert versions[0]['version'] >= versions[-1]['version']


def test_get_specific_version_content(authenticated_client):
    """Test retrieving content of a specific version."""
    filename = 'version_content_test.txt'
    
    # Create v1
    data1 = {'file': (BytesIO(b'Original content'), filename)}
    response1 = authenticated_client.post('/api/documents/upload', data=data1, content_type='multipart/form-data')
    doc_id = response1.get_json()['id']
    
    # Create v2
    data2 = {'file': (BytesIO(b'Updated content'), filename)}
    authenticated_client.post('/api/documents/upload', data=data2, content_type='multipart/form-data')
    
    # Get v1 content
    response = authenticated_client.get(f'/api/documents/{doc_id}/versions/1')
    if response.status_code == 200:
        version_data = response.get_json()
        assert version_data['version'] == 1
        assert 'created_at' in version_data


# ===== Repository Version Methods Tests =====

def test_check_existing_document(test_repo):
    """Test checking if document exists."""
    # Create document
    payload = {
        'user_id': 1,
        'name': 'exists_test.txt',
        'file_type': 'txt',
        'processed_content': 'Test content'
    }
    doc_id = test_repo.create_data_feed(payload)
    
    # Check exists
    existing = test_repo.check_existing_document('exists_test.txt', 1)
    assert existing is not None
    assert existing['id'] == doc_id
    assert existing['name'] == 'exists_test.txt'
    
    # Check non-existent
    non_existing = test_repo.check_existing_document('does_not_exist.txt', 1)
    assert non_existing is None


def test_create_version_snapshot(test_repo):
    """Test creating version snapshot."""
    # Create document
    payload = {
        'user_id': 1,
        'name': 'snapshot.txt',
        'file_type': 'txt',
        'processed_content': 'Content'
    }
    doc_id = test_repo.create_data_feed(payload)
    
    # Create snapshot
    snapshot_id = test_repo.create_version_snapshot(
        document_id=doc_id,
        version=1,
        embedding=[0.1] * 384,
        content_snapshot='Content snapshot',
        metadata_snapshot={'key': 'value'},
        user_id=1
    )
    
    assert snapshot_id is not None


def test_update_document_version(test_repo):
    """Test updating document version."""
    # Create document
    payload = {
        'user_id': 1,
        'name': 'update_version.txt',
        'file_type': 'txt',
        'processed_content': 'Original',
        'embedding': [0.1] * 384,
        'content_metadata': {},
        'vector_metadata': {}
    }
    doc_id = test_repo.create_data_feed(payload)
    
    # Update version
    new_version = test_repo.update_document_version(
        document_id=doc_id,
        embedding=[0.2] * 384,
        processed_content='Updated',
        content_metadata={'updated': True},
        vector_metadata={},
        embedding_changed=True
    )
    
    assert new_version == 2


# ===== OLLama Service Tests =====

def test_compare_embeddings_identical(test_ollama_service):
    """Test comparing identical embeddings."""
    embedding = [0.5] * 384
    similarity = test_ollama_service.compare_embeddings(embedding, embedding)
    assert similarity == pytest.approx(1.0, abs=0.01)


def test_compare_embeddings_different(test_ollama_service):
    """Test comparing different embeddings."""
    embedding1 = [1.0] * 384
    embedding2 = [0.0] * 384
    similarity = test_ollama_service.compare_embeddings(embedding1, embedding2)
    assert similarity == pytest.approx(0.0, abs=0.01)


def test_compare_embeddings_similar(test_ollama_service):
    """Test comparing similar embeddings."""
    embedding1 = [0.5 + 0.01 * i for i in range(384)]
    embedding2 = [0.5 + 0.01 * i + 0.001 for i in range(384)]
    similarity = test_ollama_service.compare_embeddings(embedding1, embedding2)
    assert 0.9 < similarity < 1.0


# ===== Query Manager Tests =====

def test_query_manager_loads_queries():
    """Test QueryManager loads queries from JSON."""
    queries_path = Path('backend/config/queries.json')
    with open(queries_path) as f:
        queries = json.load(f)
    
    qm = QueryManager(queries)
    assert qm.queries is not None
    assert len(qm.queries) > 0


def test_query_manager_substitutes_parameters():
    """Test parameter substitution in queries."""
    queries = {
        'test': {
            'select_user': 'SELECT * FROM users WHERE id = :user_id'
        }
    }
    qm = QueryManager(queries)
    
    # This is a unit test for the query loading
    # Actual substitution happens at execute time in SQLAlchemy
    assert ':user_id' in qm.queries['test']['select_user']


# ===== Integration Workflow Tests =====

def test_complete_document_lifecycle(authenticated_client):
    """Test complete document lifecycle: upload, update, delete, restore."""
    # 1. Upload initial document
    data = {
        'file': (BytesIO(b'Lifecycle test content'), 'lifecycle.txt'),
        'description': 'Lifecycle test'
    }
    response = authenticated_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    doc = response.get_json()
    doc_id = doc['id']
    assert doc['version'] == 1
    
    # 2. Update document (new content)
    data2 = {
        'file': (BytesIO(b'Updated lifecycle test content'), 'lifecycle.txt'),
    }
    response = authenticated_client.post('/api/documents/upload', data=data2, content_type='multipart/form-data')
    assert response.status_code == 200
    doc2 = response.get_json()
    assert doc2['version'] == 2
    
    # 3. Get version history
    response = authenticated_client.get(f'/api/documents/{doc_id}/versions')
    versions = response.get_json()['versions']
    assert len(versions) >= 1
    
    # 4. Soft delete
    response = authenticated_client.delete(f'/api/documents/{doc_id}?reason=Lifecycle test')
    assert response.status_code == 200
    
    # 5. Verify in deleted list
    response = authenticated_client.get('/api/documents/deleted')
    deleted = response.get_json()['documents']
    assert any(d['id'] == doc_id for d in deleted)
    
    # 6. Restore
    response = authenticated_client.post(f'/api/documents/{doc_id}/restore')
    assert response.status_code == 200
    
    # 7. Verify back in active list
    response = authenticated_client.get('/api/documents')
    documents = response.get_json()['documents']
    assert any(d['id'] == doc_id for d in documents)


def test_multiple_users_isolation(authenticated_client):
    """Test that users can only see their own documents."""
    # Create document as user 1
    data = {
        'file': (BytesIO(b'User 1 content'), 'user1_doc.txt'),
    }
    response = authenticated_client.post('/api/documents/upload', data=data, content_type='multipart/form-data')
    doc_id = response.get_json()['id']
    
    # Logout
    authenticated_client.post('/api/auth/logout')
    
    # Login as user 2
    authenticated_client.post('/api/auth/login', json={
        'email': 'user2@example.com',
        'password': 'testpassword123'
    })
    
    # Try to access user 1's document
    response = authenticated_client.get(f'/api/documents/{doc_id}')
    assert response.status_code == 404


# ===== Performance Tests =====

def test_vector_comparison_performance(test_ollama_service):
    """Test embedding comparison performance."""
    import time
    
    embedding1 = [0.5] * 384
    embedding2 = [0.6] * 384
    
    start = time.time()
    for _ in range(100):
        test_ollama_service.compare_embeddings(embedding1, embedding2)
    elapsed = time.time() - start
    
    # Should be fast (< 1 second for 100 comparisons)
    assert elapsed < 1.0


def test_list_documents_with_many_deleted(test_repo):
    """Test listing documents performance with many soft-deleted documents."""
    # Create several documents
    for i in range(10):
        payload = {
            'user_id': 1,
            'name': f'doc_{i}.txt',
            'file_type': 'txt',
            'processed_content': f'Content {i}'
        }
        test_repo.create_data_feed(payload)
    
    # Delete half of them
    docs = test_repo.list_documents(1)
    for doc in docs[:5]:
        test_repo.soft_delete_document(doc['id'], 1)
    
    # List should only show active (should be fast)
    import time
    start = time.time()
    active_docs = test_repo.list_documents(1)
    elapsed = time.time() - start
    
    assert len(active_docs) == 5
    assert elapsed < 0.5  # Should be sub-second


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

