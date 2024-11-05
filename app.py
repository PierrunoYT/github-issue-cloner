import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from github_utils import (
    validate_token, parse_issue_url, parse_fork_url,
    check_issues_enabled, get_source_issue, create_target_issue,
    GitHubError
)

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clone-issue', methods=['POST'])
def clone_issue():
    data = request.json
    issue_url = data.get('issue_url')
    target_fork_url = data.get('target_fork_url')
    
    if not GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not set in .env file'}), 400
    
    if not validate_token(GITHUB_TOKEN):
        return jsonify({'error': 'Invalid GitHub token'}), 401
    
    if not issue_url or not target_fork_url:
        return jsonify({'error': 'Missing issue URL or target fork URL'}), 400
    
    try:
        # Parse the issue URL to get components
        source_owner, source_repo, issue_number = parse_issue_url(issue_url)
        
        # Parse the target fork URL
        target_owner, target_repo = parse_fork_url(target_fork_url)
        
        # Check if issues are enabled in target repository
        if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
            return jsonify({'error': 'Issues are disabled in the target repository'}), 400
        
        # Get the source issue
        issue = get_source_issue(GITHUB_TOKEN, source_owner, source_repo, issue_number)
        
        # Create the issue in target repository
        new_issue = create_target_issue(GITHUB_TOKEN, target_owner, target_repo, issue)
        
        return jsonify({
            'message': 'Issue successfully cloned!',
            'new_issue_url': new_issue['html_url']
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except GitHubError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
import os
import re
import requests
from typing import Tuple, Dict, Optional, Any

GITHUB_API = "https://api.github.com"

class GitHubError(Exception):
    """Custom exception for GitHub API errors"""
    pass

def validate_token(token: str) -> bool:
    """Validate GitHub token by making a test API call"""
    headers = get_headers(token)
    response = requests.get(f"{GITHUB_API}/user", headers=headers)
    return response.status_code == 200

def get_headers(token: str) -> Dict[str, str]:
    """Generate headers with the provided token."""
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

def check_issues_enabled(token: str, owner: str, repo: str) -> bool:
    """Check if issues are enabled in the target repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    headers = get_headers(token)
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        raise GitHubError(f"Repository {owner}/{repo} not found")
    elif response.status_code != 200:
        raise GitHubError(f"Failed to check repository: {response.status_code}")
        
    repo_data = response.json()
    return repo_data.get('has_issues', False)

def parse_issue_url(url: str) -> Tuple[str, str, str]:
    """Parse GitHub issue URL to extract owner, repo, and issue number."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub issue URL format. Expected: https://github.com/owner/repo/issues/number")
    return match.groups()

def parse_fork_url(url: str) -> Tuple[str, str]:
    """Parse GitHub repository URL to extract owner and repo."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format. Expected: https://github.com/owner/repo")
    return match.groups()

def get_source_issue(token: str, owner: str, repo: str, issue_number: str) -> Optional[Dict[str, Any]]:
    """Fetch specific issue from source repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
    headers = get_headers(token)
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        raise GitHubError(f"Issue #{issue_number} not found in {owner}/{repo}")
    elif response.status_code == 403:
        raise GitHubError("Rate limit exceeded or insufficient permissions")
    elif response.status_code != 200:
        raise GitHubError(f"Failed to fetch issue: {response.status_code}")
    
    return response.json()

def create_target_issue(token: str, target_owner: str, target_repo: str, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create issue in target repository."""
    url = f"{GITHUB_API}/repos/{target_owner}/{target_repo}/issues"
    headers = get_headers(token)
    
    new_issue = {
        'title': issue_data['title'],
        'body': f"{issue_data['body']}\n\n---\n*Cloned from original issue: {issue_data['html_url']}*",
        'labels': [label['name'] for label in issue_data.get('labels', [])],
    }
    
    response = requests.post(url, headers=headers, json=new_issue)
    
    if response.status_code == 403:
        raise GitHubError("Rate limit exceeded or insufficient permissions")
    elif response.status_code != 201:
        raise GitHubError(f"Failed to create issue: {response.status_code}")
    
    return response.json()
