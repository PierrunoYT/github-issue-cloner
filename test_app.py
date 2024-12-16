"""Tests for the GitHub Issue Cloner application."""
import pytest
from app import app
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    """Create a test client for the application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test the index route returns successfully."""
    response = client.get('/')
    assert response.status_code == 200

def test_clone_issue_invalid_json(client):
    """Test handling of invalid JSON payload."""
    response = client.post('/clone-issue', data='invalid json')
    assert response.status_code == 400
    assert b'Request must be JSON' in response.data

def test_clone_issue_missing_fields(client):
    """Test handling of missing required fields."""
    response = client.post('/clone-issue', 
                         json={},
                         content_type='application/json')
    assert response.status_code == 400
    assert b'Issue URL is required' in response.data

def test_clone_issue_invalid_urls(client):
    """Test handling of invalid GitHub URLs."""
    test_cases = [
        {
            'issue_url': 'http://invalid-url.com',
            'target_fork_url': 'https://github.com/valid/repo'
        },
        {
            'issue_url': 'https://github.com/valid/repo/issues/1',
            'target_fork_url': 'http://invalid-url.com'
        }
    ]
    
    for test_case in test_cases:
        response = client.post('/clone-issue',
                             json=test_case,
                             content_type='application/json')
        assert response.status_code == 400
        assert b'Invalid' in response.data

@patch('app.validate_token')
@patch('app.check_issues_enabled')
@patch('app.get_source_issue')
@patch('app.create_target_issue')
@patch('app.issue_exists')
def test_successful_clone(mock_exists, mock_create, mock_get, mock_check, mock_validate, client):
    """Test successful issue cloning."""
    # Mock all the GitHub API responses
    mock_validate.return_value = True
    mock_check.return_value = True
    mock_exists.return_value = False
    mock_get.return_value = {
        'title': 'Test Issue',
        'body': 'Test Body'
    }
    mock_create.return_value = {
        'html_url': 'https://github.com/target/repo/issues/1'
    }
    
    response = client.post('/clone-issue',
                          json={
                              'issue_url': 'https://github.com/source/repo/issues/1',
                              'target_fork_url': 'https://github.com/target/repo'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'new_issue_url' in data
    assert data['new_issue_url'] == 'https://github.com/target/repo/issues/1'

@patch('app.validate_token')
def test_invalid_token(mock_validate, client):
    """Test handling of invalid GitHub token."""
    mock_validate.return_value = False
    
    response = client.post('/clone-issue',
                          json={
                              'issue_url': 'https://github.com/source/repo/issues/1',
                              'target_fork_url': 'https://github.com/target/repo'
                          },
                          content_type='application/json')
    
    assert response.status_code == 401
    assert b'Invalid GitHub token' in response.data
